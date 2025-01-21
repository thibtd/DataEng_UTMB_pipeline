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

end_docker:
	bash bash_files/take_down.sh

run_dag:
	airflow dags trigger utmb_flow

all: install lint test format start_docker end_docker run_dag