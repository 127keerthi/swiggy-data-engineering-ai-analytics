# Airflow Configuration

Airflow generates local configuration files when the environment is initialized.

The generated files irflow.cfg and .user.yml are intentionally excluded from this repository because they may contain environment-specific settings or generated secrets.

The project uses:

- irflow/Dockerfile
- irflow/docker-compose.yaml
- irflow/docker-compose.override.yml
- irflow/dags/swiggy_pipeline.py

to define the reproducible Airflow environment.

When setting up the project on another machine, start the Airflow environment using the Docker Compose configuration. Airflow will generate its required local configuration automatically.
