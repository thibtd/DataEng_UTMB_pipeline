install: 
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	python -m pytest -vvv
	
format:
	black ./**/*.py


lint:
	pylint --disable=R,C ./**/*.py

start_docker:
	bash bash_files/start.sh

stop_docker:
	bash bash_files/take_down.sh

run_dag:
	# make sure the DAG is not pause 
	docker exec -ti utmb_data_eng-airflow-webserver-1 airflow dags unpause utmb_flow 
	# trigger and run the DAG
	docker exec -ti utmb_data_eng-airflow-webserver-1 airflow dags trigger utmb_flow
	# verify that it is running
	docker exec -ti utmb_data_eng-airflow-webserver-1 airflow dags list-runs -d utmb_flow

all: install lint test format start_docker end_docker run_dag