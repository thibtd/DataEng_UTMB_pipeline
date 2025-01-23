#!/bin/bash

echo "Waiting for Airflow webserver..."
while ! curl -s "http://localhost:8080/health" > /dev/null; do
    sleep 5
done
echo "Airflow webserver is ready!"
