#!/bin/bash

echo "Starting local test run..."

source .venv/bin/activate
# Start Docker containers
make start_docker


# Run the DAG
echo "Running DAG..."
make run_dag_local

# give some time for the DAG to complete
#sleep 30

# Monitor DAG completion
MAX_WAIT=300  # 5 minutes timeout
INTERVAL=10   # Check every 10 seconds
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check specifically the last run status
    STATUS=$(docker exec utmb_data_eng-airflow-webserver-1 airflow dags list-runs -d utmb_flow --no-backfill | grep -E "success|failed|running" || echo "pending")
    
    if [[ $STATUS == *"success"* ]]; then
        echo "Last DAG run completed successfully"
        break
    elif [[ $STATUS == *"failed"* ]]; then
        echo "Last DAG run failed"
        make stop_docker
        exit 1
    elif [[ $STATUS == *"running"* ]]; then
        echo "DAG is still running... ($ELAPSED seconds elapsed)"
    else
        echo "Waiting for DAG to start... ($ELAPSED seconds elapsed)"
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "Timeout waiting for DAG completion"
    make stop_docker
    exit 1
fi

# Check results
echo "Checking results..."
if [ -f "data/utmb_data_clean.csv" ] && [ -f "data/utmb_db.duckdb" ]; then
    echo "Data files generated successfully!"
else
    echo "Error: Data files not found"
fi

# Stop containers
make stop_docker
