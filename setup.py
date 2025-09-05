from setuptools import setup
import versioneer

setup(
    name="morphocluster",
    packages=["morphocluster"],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    include_package_data=True,
    install_requires=[
        "flask>=3.0.0",
        "werkzeug>=3.0.0",
        "markupSafe>=2.1.0",
        "Jinja2>=3.1.0",
        "itsdangerous>=2.1.0",
        "psycopg2-binary>=2.9.0",
        "pandas<2.2.0",
        "sqlalchemy>=2.0.0",
        "h5py>=3.10.0",
        "scikit-learn>=1.7.0",
        "scipy",
        "redis>=3.5.0",
        "hiredis",
        "flask-restful",
        "alembic>=1.13.0",
        "Flask-SQLAlchemy>=3.1.0",
        "flask-redis",
        "Flask-Migrate>=4.0.0",
        "timer_cm",
        "fire",
        "marshmallow",
        "match_arrays",
        "Flask-RQ2",
        "tqdm",
        "hdbscan",
        "chardet",
        "environs",  # For envvar parsing
        "joblib==1.1.0",
        "Pillow",
        "numpy==1.22.*",
    ],
    extras_require={
        "tests": ["pytest", "requests", "pytest-cov", "lovely-pytest-docker"],
        "dev": ["black"],
    },
    # Console scripts removed - use Flask CLI commands instead (flask --help)
)
