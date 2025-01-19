from airflow.decorators import dag, task
from datetime import datetime
import os 
import sys 

sys.path.insert (0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.utmb_pipeline import utmb_extract_page, utmb_extract_data,utmb_transform_data, utmb_clean_data


@dag(start_date= datetime(2025,1,15),schedule=None, catchup=False,
    default_args={"owner": "Thibaut Donis"})
def utmb_flow():
    @task #extract from utmb using request
    def utmb_extract():
        url = "https://utmb.world/utmb-world-series-events"
        page = utmb_extract_page(url)
        data = utmb_extract_data(page)

    @task()#transform data 
    def utmb_transform(data):
        data_transformed = utmb_transform_data(data)
        data_cleaned = utmb_clean_data(data_transformed)

    @task() #load data to csv
    def utmb_load(data):
        data_cleaned.to_csv("data/utmb_data_clean.csv",index=False)
    raw_data = utmb_extract()
utmb_flow()