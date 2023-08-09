from getpass import getpass

import click
import flask_migrate
import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import select
from timer_cm import Timer
from werkzeug.security import generate_password_hash

from morphocluster import models
from morphocluster.dataset import Dataset
from morphocluster.project import Project
from morphocluster.extensions import database
from morphocluster.tree import Tree


def _add_user(username, password):
    pwhash = generate_password_hash(
        password, method="pbkdf2:sha256:10000", salt_length=12
    )

    with database.engine.connect() as conn:
        stmt = models.users.insert({"username": username, "pwhash": pwhash})
        conn.execute(stmt)


def init_app(app):
    # pylint: disable=unused-variable

    @app.cli.command()
    def reset_db():
        """
        Drop all tables and recreate.
        """
        print("Resetting the database.")
        print("WARNING: This is a destructive operation and all data will be lost.")

        if input("Continue? (y/n) ") != "y":
            print("Canceled.")
            return

        with database.engine.begin() as txn:
            database.metadata.drop_all(txn)
            database.metadata.create_all(txn)

            flask_migrate.stamp()

    @app.cli.command()
    def clear_cache():
        """
        Clear cached values.
        """
        with database.engine.begin() as txn:
            # Cached values are prefixed with an underscore
            cached_columns = list(
                c for c in models.nodes.columns.keys() if c.endswith("_")
            )
            values = {c: None for c in cached_columns}
            values["cache_valid"] = False
            stmt = models.nodes.update().values(values)
            txn.execute(stmt)

        print("Cache was cleared.")

    ###
    # dataset subcommand
    ###
    @app.cli.group()
    def dataset():
        pass

    @dataset.command()
    @click.argument("dataset_id", type=int)
    @click.argument("archive_fn")
    def load_objects(dataset_id, archive_fn):
        """Load objects from a .zip file."""
        connection = database.get_connection()

        with connection.begin():
            dataset = Dataset(dataset_id)
            dataset.load_objects(archive_fn)

    @dataset.command()
    @click.argument("dataset_id", type=int)
    @click.argument("features_fns", nargs=-1)
    def load_features(dataset_id, features_fns):
        """Load object features from an HDF5 file."""
        connection = database.get_connection()

        with connection.begin():
            dataset = Dataset(dataset_id)

            for feature_fn in features_fns:
                dataset.load_object_features(feature_fn)

    @dataset.command()
    @click.argument("dataset_id", type=int)
    @click.confirmation_option(prompt="Are you sure you want to delete the dataset?")
    def delete(dataset_id):
        """Delete dataset."""
        connection = database.get_connection()

        with connection.begin():
            dataset = Dataset(dataset_id)
            dataset.remove()

    @dataset.command("create")
    @click.argument("name")
    @click.argument("owner")
    @click.option("--objects", "objects_fn")
    @click.option("--features", "features_fn")
    def create_dataset(name, owner, objects_fn, features_fn):
        """Create a dataset."""

        connection = database.get_connection()

        with connection.begin():
            dataset = Dataset.create(name, owner)

            if objects_fn:
                dataset.load_objects(objects_fn)

            if features_fn:
                dataset.load_object_features(features_fn)

        print(
            "Created dataset: {} (id {:d}) for {}.".format(
                name, dataset.dataset_id, owner
            )
        )

    ###
    # project subcommand
    ###
    @app.cli.group()
    def project():
        pass

    @project.command("create")
    @click.argument("name")
    @click.argument("dataset_id", type=int)
    @click.option("--tree", "tree_fn")
    @click.option("--consolidate/--no-consolidate", default=True)
    def create_project(name, dataset_id, tree_fn, consolidate):
        """Create a project."""

        connection = database.get_connection()

        with connection.begin():
            with Project.create(name, dataset_id).lock() as project:

                if tree_fn:
                    project.import_tree(tree_fn)

                    root_id = project.get_root_id()

                    if consolidate:
                        print("Consolidating ...")
                        project.consolidate_node(
                            root_id, depth=-1, exact_vector="exact"
                        )

        print(
            "Created project {} (id {:d}) in dataset {}.".format(
                name, project.project_id, dataset_id
            )
        )

    def _load_new_objects(
        index: pd.DataFrame, batch_size: int, conn, zf: zipfile.ZipFile, images_dir: str
    ):
        if not index.size:
            return

        print(f"Loading {len(index):,d} new objects...")
        index_iter = index.itertuples()
        progress = tqdm.tqdm(total=len(index), unit_scale=True)
        while True:
            chunk = tuple(
                row._asdict() for row in itertools.islice(index_iter, batch_size)
            )
            if not chunk:
                break

            chunk_len = len(chunk)

            conn.execute(
                models.objects.insert(),  # pylint: disable=no-value-for-parameter
                [dict(row) for row in chunk],
            )

            for row in chunk:
                zf.extract(row["path"], images_dir)

            progress.update(chunk_len)
        progress.close()

    def _update_existing_objects(
        index: pd.DataFrame, batch_size: int, conn, zf: zipfile.ZipFile, images_dir: str
    ):
        if not index.size:
            return

        stmt = (
            models.objects.update()
            .where(models.objects.c.object_id == bindparam("_object_id"))
            .values({"path": bindparam("path")})
        )

        print(f"Updating {len(index):,d} existing objects...")
        index_iter = index.itertuples()
        progress = tqdm.tqdm(total=len(index), unit_scale=True)
        while True:
            chunk = tuple(
                row._asdict() for row in itertools.islice(index_iter, batch_size)
            )
            if not chunk:
                break

            chunk_len = len(chunk)

            # Update path
            conn.execute(
                stmt,
                [
                    {"_object_id": str(row["object_id"]), "path": row["path"]}
                    for row in chunk
                ],
            )

            for row in chunk:
                zf.extract(row["path"], images_dir)

                if row["path"] != row["path_old"]:
                    try:
                        os.remove(row["path_old"])
                    except FileNotFoundError:
                        print("Missing previous image:", row["path_old"])
                        pass

            progress.update(chunk_len)
        progress.close()

    @app.cli.command()
    @click.argument("root_id", type=int)
    @click.argument("tree_fn")
    def export_tree(root_id, tree_fn):
        """
        Export the whole tree with its objects.
        """
        with database.engine.connect() as conn:
            tree = Tree(conn)

            tree.export_tree(root_id, tree_fn)

    @app.cli.command()
    @click.argument("root_id", type=int, required=False)
    @click.option("--log/--no-log", "log", default=False)
    def progress(root_id, log):
        """
        Report progress on a tree
        """
        with database.engine.connect() as conn:
            tree = Tree(conn)

            if root_id is None:
                root_ids = [p["node_id"] for p in tree.get_projects()]
            else:
                root_ids = [root_id]

            with Timer("Progress") as timer:
                for rid in root_ids:
                    print("Root {}:".format(rid))
                    with timer.child(str(rid)):
                        prog = tree.calculate_progress(rid)

                    for k in sorted(prog.keys()):
                        print("{}: {}".format(k, prog[k]))

    def _validate_consolidate_project_id(ctx, param, value):
        # We don't need these
        del ctx
        del param

        if value in ("all", "visible"):
            return value

        try:
            return int(value)
        except ValueError:
            raise click.BadParameter(
                'project_id can be "all", "visible" or an actual id.'
            )

    @app.cli.command()
    @click.argument(
        "project_id", default="visible", callback=_validate_consolidate_project_id
    )
    def consolidate(project_id):
        with Timer("Consolidate") as timer:
            if project_id == "all":
                print("Consolidating all projects...")
                # root_ids = [p["node_id"] for p in tree.get_projects()]
                raise NotImplementedError()
            elif project_id == "visible":
                print("Consolidating visible projects...")
                # root_ids = [p["node_id"] for p in tree.get_projects(True)]
                raise NotImplementedError()
            else:
                project_ids = [project_id]

            for pid in project_id:
                with timer.child(str(pid)):
                    print(f"Consolidating project {pid}...")
                    with Project(pid).lock() as project:
                        project.consolidate()
            print("Done.")

    ###
    # user subcommand
    ###
    @app.cli.group()
    def user():
        pass

    @user.command("add")
    @click.argument("username")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def user_add(username, password):
        print("Adding user {}:".format(username))

        if not password:
            print("Password must not be empty!")
            return

        try:
            _add_user(username, password)
        except IntegrityError as e:
            print(e)
        else:
            print(f"User {username} added.")

    @app.cli.command()
    @click.argument("username")
    def change_user(username):
        print("Changing user {}:".format(username))

        if not password:
            print("Password must not be empty!")
            return

        pwhash = generate_password_hash(
            password, method="pbkdf2:sha256:10000", salt_length=12
        )

        try:
            with database.engine.connect() as conn:
                stmt = models.users.insert({"username": username, "pwhash": pwhash})
                conn.execute(stmt)
        except IntegrityError as e:
            print(e)
        else:
            print(f"User {username} changed.")

    @app.cli.command()
    @click.argument("root_id")
    @click.argument("classification_fn")
    def export_classifications(root_id, classification_fn):
        with database.engine.connect() as conn:
            tree = Tree(conn)
            root_id = tree.get_root_id(project_id)
            processing_tree = tree.dump_tree(root_id)
            df = processing_tree.to_flat(clean_name=clean_name)
            df.to_csv(labels_fn, index=False)

    @app.cli.command()
    @click.argument("node_id")
    @click.argument("filename")
    def export_direct_objects(node_id, filename):
        with database.engine.connect() as conn, open(filename, "w") as f:
            tree = Tree(conn)

            f.writelines(
                "{}\n".format(o["object_id"]) for o in tree.get_objects(node_id)
            )

    @app.cli.command()
    @click.argument("filename")
    def export_log(filename):
        with database.engine.connect() as conn:
            log = pd.read_sql_query(
                select([models.log, models.nodes.c.project_id]).select_from(
                    models.log.outerjoin(models.nodes)
                ),
                conn,
                index_col="log_id",
            )
            log.to_csv(filename)

    @app.cli.command()
    def truncate_log():
        """
        Truncate the log.
        """
        print("Truncate log")
        print("WARNING: This is a destructive operation and all data will be lost.")

        if input("Continue? (y/n) ") != "y":
            print("Canceled.")
            return

        with database.engine.connect() as conn:
            stmt = models.log.delete()
            conn.execute(stmt)
