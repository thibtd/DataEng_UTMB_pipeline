#!/bin/bash

echo "Starting local test run..."

source .venv/bin/activate
# Start Docker containers
make start_docker
make wait_for_airflow

# Run the DAG
echo "Running DAG..."
make run_dag_local

# give some time for the DAG to complete
sleep 120


# Check results
echo "Checking results..."
if [ -f "data/utmb_data_clean.csv" ] && [ -f "data/utmb_db.duckdb" ]; then
    echo "Data files generated successfully!"
else
    echo "Error: Data files not found"
fi

# Stop containers
make stop_docker
