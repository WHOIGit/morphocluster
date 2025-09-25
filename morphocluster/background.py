import datetime as dt
import os
import zipfile
import csv
import time
from pathlib import Path

import flask_rq2
from flask import current_app as app

from morphocluster.extensions import database, rq
from morphocluster.processing.recluster import Recluster
from morphocluster.processing.tree import Tree as ProcessingTree
from morphocluster.tree import Tree


def validate_background_job(fun):
    return isinstance(getattr(fun, "helper", None), flask_rq2.functions.JobFunctions)


@rq.job
def add(x, y):
    return x + y


@rq.job
def export_project(project_id):
    config = app.config

    # Dump the database tree
    with database.engine.connect() as conn:
        db_tree = Tree(conn)
        root_id = db_tree.get_root_id(project_id)
        project = db_tree.get_project(project_id)
        tree = db_tree.dump_tree(root_id)

    tree_fn = os.path.join(
        config["FILES_DIR"],
        "{:%Y-%m-%d-%H-%M-%S}--{}--{}.zip".format(
            dt.datetime.now(), project["project_id"], project["name"]
        ),
    )

    tree.save(tree_fn)

    return tree_fn


@rq.job(timeout=43200)
def recluster_project(project_id, min_cluster_size):
    """
    Timeout: 12h
    """

    config = app.config

    # Dump the database tree
    print("Dumping database tree...")
    with database.engine.connect() as conn:
        db_tree = Tree(conn)
        root_id = db_tree.get_root_id(project_id)
        project = db_tree.get_project(project_id)
        tree = db_tree.dump_tree(root_id)

    # Recluster unapproved objects
    print("Reclustering...")
    recluster = Recluster()
    recluster.load_tree(tree)

    for features_fn in config["RECLUSTER_FEATURES"]:
        recluster.load_features(features_fn)

    # Cluster 1M objects maximum
    # sample_size = int(1e6)
    sample_size = 1000

    recluster.cluster(
        ignore_approved=True,
        sample_size=sample_size,
        min_cluster_size=min_cluster_size,
        min_samples=1,
        cluster_selection_method="leaf",
    )

    tree = recluster.merge_trees()

    # Load new tree into the database
    print("Loading tree into database...")
    project_name = "{}-{}".format(project["name"], min_cluster_size)

    with database.engine.connect() as conn:
        db_tree = Tree(conn)

        with conn.begin():
            project_id = db_tree.load_project(project_name, tree)
            root_id = db_tree.get_root_id(project_id)

            print("Consolidating ...")
            db_tree.consolidate_node(root_id)

        print("Root ID: {}".format(root_id))
        print("Project ID: {}".format(project_id))

    print("Done.")


# ===============================================================================
# Upload Pipeline Background Jobs
# ===============================================================================

@rq.job(timeout=3600)  # 1 hour timeout
def extract_features_job(filename, parameters=None):
    """
    Background job for extracting features from uploaded archive using MorphoCluster's real feature extraction.
    """
    print(f"Starting feature extraction for {filename}")

    # Get current job for progress updates
    from rq import get_current_job
    from morphocluster.processing.extract_features import extract_features
    import zipfile

    job = get_current_job()

    if parameters is None:
        parameters = {}

    # Create application context for Flask app access
    from morphocluster import create_app
    app_instance = create_app()
    with app_instance.app_context():
        try:
            files_dir = Path(app_instance.config["FILES_DIR"])
            archive_path = files_dir / filename

            if not archive_path.exists():
                raise FileNotFoundError(f"Archive {filename} not found")

            # Create features output filename
            features_filename = f"{archive_path.stem}_features.h5"
            features_path = archive_path.parent / features_filename

            # Step 1: Validate archive
            job.meta['status'] = 'validating'
            job.meta['progress'] = 5
            job.meta['current_step'] = 'Validating archive structure...'
            job.save_meta()

            # Check if archive has index.csv
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"Archive contents: {file_list[:10]}...")  # Show first 10 files for debugging

                if 'index.csv' not in file_list:
                    # Check if this is an unconverted EcoTaxa file - suggest conversion
                    ecotaxa_files = [f for f in file_list if f.startswith('ecotaxa_') and f.endswith('.tsv')]
                    if ecotaxa_files:
                        raise ValueError(f"Archive appears to be in EcoTaxa format (found {ecotaxa_files[0]}). Please convert it first.")
                    else:
                        raise ValueError(f"Archive must contain index.csv file. Found files: {', '.join(file_list[:5])}")

                image_files = [f for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif'))]
                total_images = len(image_files)

            print(f"Archive validation passed. Found {total_images} images")

            # Step 2: Setup parameters
            job.meta['progress'] = 10
            job.meta['current_step'] = 'Setting up feature extraction parameters...'
            job.save_meta()

            # Extract parameters with defaults
            normalize = parameters.get('normalize', True)
            batch_size = parameters.get('batch_size', 512)
            model_file = parameters.get('model_file', None)

            # Set default model file if not specified
            if model_file is None:
                model_file = '/code/data/model_state.pth'

            # Parse input_mean and input_std - handle both string and list formats
            def parse_mean_std(value, default):
                if isinstance(value, str):
                    if value.strip():
                        return tuple(map(float, value.split(',')))
                    else:
                        return default
                elif isinstance(value, (list, tuple)):
                    return tuple(value)
                else:
                    return default

            input_mean = parse_mean_std(parameters.get('input_mean'), (0, 0, 0))
            input_std = parse_mean_std(parameters.get('input_std'), (1, 1, 1))

            print(f"Using parameters: normalize={normalize}, batch_size={batch_size}, model_file={model_file}")
            print(f"Input normalization: mean={input_mean}, std={input_std}")

            # Step 3: Start feature extraction
            job.meta['progress'] = 15
            job.meta['current_step'] = 'Starting feature extraction (this may take several minutes)...'
            job.meta['total_images'] = total_images
            job.save_meta()

            # Run MorphoCluster's real feature extraction
            extract_features(
                archive_fn=str(archive_path),
                features_fn=str(features_path),
                parameters_fn=model_file,  # None for pretrained ImageNet
                normalize=normalize,
                batch_size=batch_size,
                cuda=True,  # Use GPU if available
                input_mean=input_mean,
                input_std=input_std
            )

            # Step 4: Complete
            job.meta['status'] = 'completed'
            job.meta['progress'] = 100
            job.meta['current_step'] = 'Feature extraction completed'
            job.meta['completed_at'] = dt.datetime.now().isoformat()

            # Create result with actual feature file info
            result = {
                'feature_file': features_filename,
                'feature_path': str(features_path),
                'total_images': total_images,
                'feature_dimensions': 32,  # ResNet18 with 32-dim bottleneck
                'model_used': f'ResNet18 with 32-dim bottleneck: {model_file}',
                'normalize': normalize,
                'batch_size': batch_size
            }

            job.meta['result'] = result
            job.save_meta()

            print(f"Feature extraction completed for {filename}")
            print(f"Features saved to: {features_path}")
            return result

        except Exception as e:
            print(f"Feature extraction failed: {str(e)}")
            job.meta['status'] = 'failed'
            job.meta['error_message'] = str(e)
            job.meta['failed_at'] = dt.datetime.now().isoformat()
            job.save_meta()
            raise


@rq.job(timeout=1800)  # 30 minutes timeout
def convert_ecotaxa_job(filename, parameters=None):
    """
    Background job for converting EcoTaxa format to standard format.
    Uses MorphoCluster's existing fix_ecotaxa functionality.
    """
    print(f"Starting EcoTaxa conversion for {filename}")

    from rq import get_current_job
    import shutil

    job = get_current_job()

    if parameters is None:
        parameters = {}

    # Create application context for Flask app access
    from morphocluster import create_app
    app_instance = create_app()
    with app_instance.app_context():
        try:
            archive_path = Path(app_instance.config["FILES_DIR"]) / filename

            if not archive_path.exists():
                raise FileNotFoundError(f"Archive {filename} not found")

            # Step 1: Analyze parameters
            job.meta['status'] = 'analyzing'
            job.meta['progress'] = 10
            job.meta['current_step'] = 'Analyzing EcoTaxa format and parameters...'
            job.save_meta()

            encoding = parameters.get('encoding')
            delimiter = parameters.get('delimiter')
            force = parameters.get('force', False)

            # Step 2: Create working copy for conversion
            job.meta['progress'] = 20
            job.meta['current_step'] = 'Creating working copy...'
            job.save_meta()

            # Create a copy to work on (fix_ecotaxa modifies in place)
            work_path = archive_path.with_suffix('.converting.zip')
            shutil.copy2(archive_path, work_path)

            # Step 3: Run EcoTaxa conversion using existing MorphoCluster function
            job.meta['progress'] = 40
            job.meta['current_step'] = 'Converting EcoTaxa format to standard format...'
            job.save_meta()

            try:
                # Call fix_ecotaxa function directly (it's a Click command)
                from click.testing import CliRunner
                from morphocluster.scripts import fix_ecotaxa

                runner = CliRunner()
                args = [str(work_path)]
                if encoding:
                    args.extend(['--encoding', encoding])
                if delimiter:
                    args.extend(['--delimiter', delimiter])
                if force:
                    args.append('--force')

                result = runner.invoke(fix_ecotaxa, args)
                if result.exit_code != 0:
                    raise RuntimeError(f"EcoTaxa conversion failed: {result.output}")
            except Exception as conversion_error:
                # Clean up working file
                if work_path.exists():
                    work_path.unlink()
                raise conversion_error

            # Step 4: Validate conversion result
            job.meta['progress'] = 80
            job.meta['current_step'] = 'Validating converted archive...'
            job.save_meta()

            # Check that index.csv was created
            import zipfile
            with zipfile.ZipFile(work_path, 'r') as zf:
                if 'index.csv' not in zf.namelist():
                    raise ValueError("Conversion failed: index.csv not created")

            # Step 5: Replace original with converted version
            job.meta['progress'] = 95
            job.meta['current_step'] = 'Finalizing converted archive...'
            job.save_meta()

            # Move converted file to final location
            converted_path = archive_path.with_name(f"{archive_path.stem}_converted{archive_path.suffix}")
            work_path.rename(converted_path)

            # Complete
            job.meta['status'] = 'completed'
            job.meta['progress'] = 100
            job.meta['current_step'] = 'EcoTaxa conversion completed'
            job.meta['completed_at'] = dt.datetime.now().isoformat()
            job.meta['result'] = {
                'converted_file': converted_path.name,
                'original_file': filename,
                'encoding': encoding,
                'delimiter': delimiter,
                'conversion_method': 'morphocluster.scripts.fix_ecotaxa'
            }
            job.save_meta()

            print(f"EcoTaxa conversion completed: {filename} -> {converted_path.name}")
            return job.meta['result']

        except Exception as e:
            print(f"EcoTaxa conversion failed: {str(e)}")
            job.meta['status'] = 'failed'
            job.meta['error_message'] = str(e)
            job.meta['failed_at'] = dt.datetime.now().isoformat()
            job.save_meta()
            raise


@rq.job(timeout=7200)  # 2 hours timeout
def initial_clustering_job(archive_name, feature_file, parameters=None):
    """
    Background job for initial clustering to create a new MorphoCluster project.
    """
    print(f"Starting initial clustering for {archive_name}")

    from rq import get_current_job

    job = get_current_job()

    if parameters is None:
        parameters = {}

    # Create application context for Flask app access
    from morphocluster import create_app
    app_instance = create_app()
    with app_instance.app_context():
        try:
            files_dir = Path(app_instance.config["FILES_DIR"])
            archive_path = files_dir / archive_name
            feature_path = files_dir / feature_file

            if not archive_path.exists():
                raise FileNotFoundError(f"Archive {archive_name} not found")
            if not feature_path.exists():
                raise FileNotFoundError(f"Feature file {feature_file} not found")

            # Step 1: Setup parameters
            job.meta['status'] = 'setting_up'
            job.meta['progress'] = 10
            job.meta['current_step'] = 'Setting up clustering parameters...'
            job.save_meta()

            # Extract parameters with defaults
            project_name = parameters.get('project_name', f"Project-{archive_path.stem}")
            description = parameters.get('description', '')
            min_cluster_size = parameters.get('min_cluster_size', 128)
            min_samples = parameters.get('min_samples', 1)
            cluster_selection_method = parameters.get('cluster_selection_method', 'leaf')
            sample_size = parameters.get('sample_size', 0)  # 0 = use all
            keep_unexplored_ratio = parameters.get('keep_unexplored_ratio', 0.0)

            print(f"Clustering parameters: min_cluster_size={min_cluster_size}, method={cluster_selection_method}")

            # Step 2: Extract images from archive
            job.meta['progress'] = 15
            job.meta['current_step'] = 'Extracting images from archive...'
            job.save_meta()

            import zipfile
            import pandas as pd
            import h5py
            import shutil
            from morphocluster import models

            # Create images directory for this archive
            images_dir = Path(app_instance.config["IMAGES_DIR"])
            archive_images_dir = images_dir / archive_path.stem
            archive_images_dir.mkdir(parents=True, exist_ok=True)

            # Read index.csv from archive to get object_id and path mappings
            with zipfile.ZipFile(archive_path, 'r') as zf:
                with zf.open('index.csv') as fp:
                    archive_df = pd.read_csv(fp, dtype=str, usecols=["object_id", "path"])

                # Extract image files
                print(f"Extracting {len(archive_df)} images to {archive_images_dir}")
                for _, row in archive_df.iterrows():
                    image_path = row['path']
                    if image_path in zf.namelist():
                        # Extract to the archive-specific directory
                        extracted_path = zf.extract(image_path, archive_images_dir)

                        # Move to flat structure if needed (some archives have subdirectories)
                        final_path = archive_images_dir / Path(image_path).name
                        if Path(extracted_path) != final_path:
                            shutil.move(extracted_path, final_path)

            # Step 3: Load objects from archive into database
            job.meta['progress'] = 25
            job.meta['current_step'] = 'Loading objects into database...'
            job.save_meta()

            # Load feature vectors from H5 file
            with h5py.File(feature_path, 'r') as h5f:
                feature_object_ids = h5f['object_id'][:]
                features = h5f['features'][:]

                # Convert bytes to strings if necessary
                if hasattr(feature_object_ids[0], 'decode'):
                    feature_object_ids = [oid.decode('utf-8') for oid in feature_object_ids]
                else:
                    feature_object_ids = list(feature_object_ids)

            feature_dims = features.shape[1] if len(features.shape) > 1 else len(features[0]) if len(features) > 0 else 0
            print(f"Archive contains {len(archive_df)} objects, features for {len(feature_object_ids)} objects")
            print(f"Feature dimensions: {feature_dims}")

            # Step 3: Insert objects into database with vectors
            job.meta['progress'] = 30
            job.meta['current_step'] = 'Inserting objects into database...'
            job.save_meta()

            # Create object data for database insertion
            object_data = []
            feature_dict = dict(zip(feature_object_ids, features))

            for _, row in archive_df.iterrows():
                object_id = row['object_id']
                original_path = row['path']
                # Update path to point to extracted image in archive subdirectory
                extracted_path = f"{archive_path.stem}/{Path(original_path).name}"
                vector = feature_dict.get(object_id)

                if vector is not None:
                    object_data.append({
                        'object_id': object_id,
                        'path': extracted_path,  # Path relative to IMAGES_DIR
                        'vector': vector  # Keep as numpy array - should be 32 dimensions now
                    })

            # Insert objects into database
            with database.engine.connect() as conn:
                with conn.begin():
                    # Check if objects already exist to avoid duplicates
                    existing_objects = conn.execute(
                        models.objects.select().where(
                            models.objects.c.object_id.in_([obj['object_id'] for obj in object_data])
                        )
                    ).fetchall()
                    existing_object_ids = {obj.object_id for obj in existing_objects}

                    # Only insert new objects
                    new_objects = [obj for obj in object_data if obj['object_id'] not in existing_object_ids]

                    if new_objects:
                        print(f"Inserting {len(new_objects)} new objects into database")
                        conn.execute(models.objects.insert(), new_objects)
                    else:
                        print("All objects already exist in database")

            # Step 4: Initialize clustering
            job.meta['progress'] = 40
            job.meta['current_step'] = 'Initializing clustering algorithm...'
            job.save_meta()

            recluster = Recluster()

            # Step 5: Load features
            job.meta['progress'] = 50
            job.meta['current_step'] = 'Loading extracted features...'
            job.save_meta()

            recluster.load_features(str(feature_path))

            # Step 6: Skip init_tree() - let clustering create the tree structure
            job.meta['progress'] = 60
            job.meta['current_step'] = 'Preparing clustering...'
            job.save_meta()

            # Note: Not calling recluster.init_tree() - this was interfering with clustering

            # Step 7: Run clustering
            job.meta['progress'] = 70
            job.meta['current_step'] = 'Running HDBSCAN clustering (this may take several minutes)...'
            job.save_meta()

            # Apply sample size and keep_unexplored_ratio if specified
            cluster_kwargs = {
                'min_cluster_size': min_cluster_size,
                'min_samples': min_samples,
                'cluster_selection_method': cluster_selection_method,
            }

            if sample_size > 0:
                cluster_kwargs['sample_size'] = sample_size
                print(f"Using sample size: {sample_size}")

            if keep_unexplored_ratio > 0:
                cluster_kwargs['keep_unexplored'] = keep_unexplored_ratio

            recluster.cluster(**cluster_kwargs)

            # Step 8: Get the clustered tree
            job.meta['progress'] = 80
            job.meta['current_step'] = 'Building project tree structure...'
            job.save_meta()

            # Get the first (and only) tree from recluster
            tree = recluster.trees[0]

            # Step 9: Load into database
            job.meta['progress'] = 90
            job.meta['current_step'] = 'Creating project in database...'
            job.save_meta()

            with database.engine.connect() as conn:
                db_tree = Tree(conn)

                with conn.begin():
                    project_id = db_tree.load_project(project_name, tree)
                    root_id = db_tree.get_root_id(project_id)

                    print("Consolidating tree structure...")
                    db_tree.consolidate_node(root_id)

            # Step 10: Complete
            job.meta['status'] = 'completed'
            job.meta['progress'] = 100
            job.meta['current_step'] = 'Project created successfully'
            job.meta['completed_at'] = dt.datetime.now().isoformat()

            # Get final statistics
            cluster_count = len(tree.nodes)  # Number of nodes/clusters
            object_count = len(tree.objects)  # Number of objects

            result = {
                'project_id': project_id,
                'project_name': project_name,
                'root_id': root_id,
                'cluster_count': cluster_count,
                'object_count': object_count,
                'min_cluster_size': min_cluster_size,
                'cluster_selection_method': cluster_selection_method,
                'project_url': f'/projects/{project_id}'
            }

            job.meta['result'] = result
            job.save_meta()

            print(f"Initial clustering completed for {archive_name}")
            print(f"Created project '{project_name}' with {cluster_count} clusters and {object_count} objects")
            return result

        except Exception as e:
            print(f"Initial clustering failed: {str(e)}")
            job.meta['status'] = 'failed'
            job.meta['error_message'] = str(e)
            job.meta['failed_at'] = dt.datetime.now().isoformat()
            job.save_meta()
            raise


@rq.job(timeout=3600)  # 1 hour timeout
def reclustering_job(project_id, parameters=None):
    """
    Background job for re-clustering an existing project.
    """
    print(f"Starting re-clustering for project {project_id}")
    from rq import get_current_job
    job = get_current_job()
    if parameters is None:
        parameters = {}

    # Create application context for Flask app access
    from morphocluster import create_app
    app_instance = create_app()

    with app_instance.app_context():
        try:
            from morphocluster.processing.recluster import Recluster
            from morphocluster.tree import Tree
            from morphocluster import models
            import datetime as dt
            from pathlib import Path
            import h5py

            # Step 1: Setup parameters
            job.meta['status'] = 'setting_up'
            job.meta['progress'] = 10
            job.meta['current_step'] = 'Setting up re-clustering parameters...'
            job.save_meta()

            # Extract parameters with defaults
            new_project_name = parameters.get('project_name', f"Re-clustered Project {project_id}")
            min_cluster_size = parameters.get('min_cluster_size', 32)
            min_samples = parameters.get('min_samples', 1)
            cluster_selection_method = parameters.get('cluster_selection_method', 'leaf')
            sample_size = parameters.get('sample_size', 0)  # 0 = use all
            keep_unexplored_ratio = parameters.get('keep_unexplored_ratio', 0.0)

            print(f"Re-clustering parameters: min_cluster_size={min_cluster_size}, method={cluster_selection_method}")

            # Step 2: Load the existing project and export it
            job.meta['progress'] = 20
            job.meta['current_step'] = 'Loading existing project...'
            job.save_meta()

            with database.engine.connect() as conn:
                db_tree = Tree(conn)
                existing_project = db_tree.get_project(project_id)
                root_id = db_tree.get_root_id(project_id)

                # Export existing tree to temporary file
                temp_tree_path = f"/tmp/temp_tree_{project_id}.zip"
                db_tree.export_tree(root_id, temp_tree_path)

            # Step 3: Find the feature file (look for existing feature files)
            job.meta['progress'] = 30
            job.meta['current_step'] = 'Finding feature file...'
            job.save_meta()

            files_dir = Path(app_instance.config["FILES_DIR"])
            # Look for feature files that might match this project
            feature_files = list(files_dir.glob("*_features.h5"))

            if not feature_files:
                raise FileNotFoundError("No feature files found for re-clustering")

            # Use the most recent feature file (or implement better matching logic)
            feature_path = max(feature_files, key=lambda x: x.stat().st_mtime)
            print(f"Using feature file: {feature_path}")

            # Step 4: Initialize clustering
            job.meta['progress'] = 40
            job.meta['current_step'] = 'Initializing re-clustering algorithm...'
            job.save_meta()

            recluster = Recluster()

            # Step 5: Load features
            job.meta['progress'] = 50
            job.meta['current_step'] = 'Loading features...'
            job.save_meta()

            recluster.load_features(str(feature_path))

            # Step 6: Load existing tree
            job.meta['progress'] = 60
            job.meta['current_step'] = 'Loading existing project tree...'
            job.save_meta()

            recluster.load_tree(temp_tree_path)

            # Step 7: Run clustering
            job.meta['progress'] = 70
            job.meta['current_step'] = 'Running HDBSCAN re-clustering...'
            job.save_meta()

            cluster_kwargs = {
                'min_cluster_size': min_cluster_size,
                'min_samples': min_samples,
                'cluster_selection_method': cluster_selection_method,
            }

            if sample_size > 0:
                cluster_kwargs['sample_size'] = sample_size

            if keep_unexplored_ratio > 0:
                cluster_kwargs['keep_unexplored'] = keep_unexplored_ratio

            recluster.cluster(**cluster_kwargs)

            # Step 8: Create new project from re-clustered tree
            job.meta['progress'] = 80
            job.meta['current_step'] = 'Creating new project...'
            job.save_meta()

            # Get the new clustered tree (should be the second tree)
            new_tree = recluster.trees[-1]  # Get the most recent tree

            # Step 9: Load into database as new project
            job.meta['progress'] = 90
            job.meta['current_step'] = 'Saving new project to database...'
            job.save_meta()

            with database.engine.connect() as conn:
                db_tree = Tree(conn)

                with conn.begin():
                    new_project_id = db_tree.load_project(new_project_name, new_tree)
                    new_root_id = db_tree.get_root_id(new_project_id)

                    print("Consolidating new tree structure...")
                    db_tree.consolidate_node(new_root_id)

            # Clean up temporary file
            Path(temp_tree_path).unlink(missing_ok=True)

            # Step 10: Complete
            job.meta['status'] = 'completed'
            job.meta['progress'] = 100
            job.meta['current_step'] = 'Re-clustering completed successfully'
            job.meta['completed_at'] = dt.datetime.now().isoformat()

            # Get final statistics
            cluster_count = len(new_tree.nodes)
            object_count = len(new_tree.objects)

            result = {
                'original_project_id': project_id,
                'new_project_id': new_project_id,
                'new_project_name': new_project_name,
                'new_root_id': new_root_id,
                'cluster_count': cluster_count,
                'object_count': object_count,
                'min_cluster_size': min_cluster_size,
                'cluster_selection_method': cluster_selection_method,
                'project_url': f'/projects/{new_project_id}'
            }

            job.meta['result'] = result
            job.save_meta()

            print(f"Re-clustering completed for project {project_id}")
            print(f"Created new project '{new_project_name}' (ID: {new_project_id}) with {cluster_count} clusters")
            return result

        except Exception as e:
            print(f"Re-clustering failed: {str(e)}")
            job.meta['status'] = 'failed'
            job.meta['error_message'] = str(e)
            job.meta['failed_at'] = dt.datetime.now().isoformat()
            job.save_meta()
            raise
