from airflow.decorators import dag, task
from datetime import datetime
import os 
import sys 
import json 

sys.path.insert (0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.utmb_pipeline import utmb_extract_page, utmb_extract_data,utmb_transform_data, utmb_clean_data


@dag(start_date= datetime(2025,1,15),schedule=None, catchup=False,
    default_args={"owner": "Thibaut Donis"})
def utmb_flow():
    @task #extract from utmb using request
    def utmb_extract():
        data_complete = []
        for p in range(1,4): #there are 3 pages with races
            page = utmb_extract_page(f"https://www.finishers.com/en/events?page={p}&tags=utmbevent")
            print(page)
            data = utmb_extract_data(page)
            print(data)
            print(len(data))
            data_complete.extend(data)
        print(len(data_complete))
        print(type(data_complete))
        utmb_extract.xcom_push(key="utmb_data", value=data_complete)
        return f"ok {len(data_complete)} events retrieved"

    @task()#transform data 
    def utmb_transform():
        
        data = utmb_transform.xcom_pull(key="utmb_data", task_ids="utmb_extract")
        print(data)
        print(type(data))
        data_transformed = utmb_transform_data(data)
        data_cleaned = utmb_clean_data(data_transformed)
        utmb_transform.xcom_push(key="utmb_data_cleaned", value=data_cleaned)
        return "OK"

    @task() #load data to csv
    def utmb_load():
        data_cleaned = utmb.load.xcom_pull(key="utmb_data_cleaned", task_ids="utmb_transform")
        data_cleaned.to_csv("data/utmb_data_clean.csv",index=False)

    utmb_extract() >> utmb_transform() >> utmb_load()
utmb_flow()