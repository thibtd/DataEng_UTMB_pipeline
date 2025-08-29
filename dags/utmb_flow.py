from airflow import XComArg
from airflow.decorators import dag, task
from datetime import datetime
import os, sys
import pandas as pd
from typing import cast

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.utmb_pipeline import (
    utmb_extract_page,
    utmb_extract_data,
    utmb_extract_clean_data,
    utmb_transform_data,
    load_data_to_db,
)


@dag(
    start_date=datetime(2025, 1, 15),
    schedule=None,
    catchup=False,
    default_args={"owner": "Thibaut Donis"},
)
def utmb_flow():
    @task  # extract from utmb using selenium and beautifulsoup
    def utmb_extract() -> list:
        data_complete = []
        for p in range(1, 4):  # there are 3 pages with races
            page = utmb_extract_page(
                f"https://www.finishers.com/en/courses?page={p}&series=utmbevent"
            )
            data = utmb_extract_data(page)
            data = utmb_extract_clean_data(data)
            data_complete.extend(data)
        return data_complete

    @task()  # transform data
    def utmb_transform(data: list) -> pd.DataFrame:
        print(data)
        print(type(data))
        data_transformed = utmb_transform_data(data)
        df = pd.DataFrame(data_transformed)
        return df

    @task()  # load data to duckdb
    def utmb_load(data_cleaned: pd.DataFrame):

        load_data_to_db(data_cleaned)

    raw_data: XComArg = utmb_extract()
    transformed_data: XComArg = utmb_transform(cast(list, raw_data))
    utmb_load(cast(pd.DataFrame, transformed_data))


utmb_flow()
