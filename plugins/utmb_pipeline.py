from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from emoji import replace_emoji
import re, os, sys, time, bs4
import duckdb
from langchain_huggingface import HuggingFaceEmbeddings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.utils import round_to_nearest_5, get_lat_long, clean_dates, get_offered_X


def utmb_extract_page(url: str, local: bool = False) -> str:
    print("Extracting data from...", url)
    options = webdriver.ChromeOptions()
    remote_webdriver = "remote_chromedriver"
    options.add_argument("--no-sandbox")
    options.add_argument("-headless")
    options.page_load_strategy = "normal"
    if local:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Remote(f"{remote_webdriver}:4444/wd/hub", options=options)
    driver.get(url)

    # Wait for dynamic content to load
    print("Waiting for page to load...")
    start_time = time.time()
    # this will trigger the error everytime but the page will load correctly and the correct data will be extracted (yey)
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "style_EventPreview__kWm7L group no-link-underline")
            )
        )
    except TimeoutException as e:
        print("the page took too long to load")

    # Wait for dynamic content to load
    page_source = driver.page_source
    driver.quit()
    end_time = time.time()
    print(f"Page loaded in {end_time-start_time} seconds")
    return page_source


def utmb_extract_data(html: str) -> bs4.element.ResultSet:
    soup = BeautifulSoup(html, "html.parser")
    events: bs4.element.ResultSet = soup.find_all(
        "a", {"class": "style_EventPreview__kWm7L group no-link-underline"}
    )
    print(f"Found {len(events)} events")
    return events


def utmb_extract_clean_data(data: bs4.element.ResultSet) -> list:
    data_cleaned: list = []
    for i in range(0, len(data)):

        row = data[i]
        values: dict = {
            "name": row.find("div", {"class": "typo-h4 leading-tight mb-1"}).text,
            "distances": row.find("div", {"class": "styles_Distances__GLSe1"}).text,
            "date": row.find(
                "div", {"class": "flex flex-row items-center style_Date__UbJPv py-1"}
            ).text,
            "date_confirmed": (
                True
                if row.find(
                    "span", {"class": "styles_Chip__5DJ6w styles_Confirmed__talWF"}
                )
                else False
            ),
            "country": row.find("div", {"class": "style_City__mrIOD"})
            .find("img")
            .get("title"),
            "city": row.find("div", {"class": "style_City__mrIOD"}).text,
            "styles": row.find(
                "div", {"class": "style_Tags__1wVj6 nice-scrollbar"}
            ).text,
            "discipline": row.find("div", {"class": "style_Disciplines__KoinH"}).text,
            "image": row.find("img").get("src") if row.find("img") else "NO IMAGE",
            "link": "https://www.finishers.com" + row.get("href"),
        }
        data_cleaned.append(values)
    return data_cleaned


def utmb_transform_data(d: list|pd.DataFrame) -> pd.DataFrame:
    data: pd.DataFrame = pd.DataFrame(d)
    # remove  "by UTMB®" in name
    data.loc[:, "name"] = data["name"].str.replace("by UTMB®", "")
    data.loc[:, "name"] = data["name"].str.replace("by UTMB ®", "")
    data.loc[:, "name"] = data["name"].str.strip()


    # in distances remove "km" and split by " " and make dummies
    data["distances"] = (
        data["distances"].str.replace("km", "").str.strip().str.split("\xa0")
    )
    unique_distances: np.ndarray = (
        data["distances"].explode().astype(float).apply(round_to_nearest_5).unique()
    )
    data["distances"] = data["distances"].apply(
        lambda d: [round_to_nearest_5(x) for x in d]
    )
    for dist in sorted(unique_distances):
        data["distance_" + str(dist)] = data["distances"].apply(
            lambda x: float(dist) in x
        )

    # in date remove "Date confirmed" and split by into year, month, day and duration (days)
    data["date"] = data["date"].str.replace("Date confirmed", "").str.strip()
    ## To finish

    # in styles remove emojis, +X and create dummies split by emoji (?)
    data["styles"] = data["styles"].apply(lambda d: re.sub(r"\+\d+", "", d)).str.strip()
    data["styles"] = data["styles"].str.replace("®", "")
    data["styles"] = (
        data["styles"]
        .apply(lambda d: replace_emoji(d, replace="\xa0"))
        .str.replace(" ", "")
        .str.strip()
        .str.split("\xa0")
    )
    styles_unique: np.ndarray = data["styles"].explode().unique()
    for style in sorted(styles_unique):
        data["style_" + str(style)] = data["styles"].apply(lambda x: style in x)

    # in discipline create dummies split on +X
    data["discipline"] = (
        data["discipline"]
        .apply(lambda d: re.sub(r"\+\d+", "\xa0", d))
        .str.strip()
        .str.split("\xa0")
    )
    discipline_unique: np.ndarray = data["discipline"].explode().unique()
    for disip in sorted(discipline_unique):
        data["discipline_" + str(disip)] = data["discipline"].apply(
            lambda x: disip in x
        )

    # clean the dates
    data[["multidays", "start_day", "end_day", "month", "year", "duration"]] = (
        data.apply(clean_dates, axis=1, result_type="expand")
    )

    # for each city find lat and long
    data[["latitude", "longitude"]] = data["city"].apply(
        lambda x: pd.Series(get_lat_long(x))
    )

    # drop the columns
    data.drop(
        columns=["distances", "styles", "discipline", "date"], axis=1, inplace=True
    )

    return data



def load_data_to_db(data: pd.DataFrame) -> None:
    """
    load the dataFrame to a duckdb instance
    """
    conn = duckdb.connect("data/utmb_db.duckdb")
    duck_tables = conn.sql("show all tables").df()
    if "UTMB" in duck_tables["name"].values:
        print("Table UTMB already exists in duckDB, it will be replaced")   
        conn.sql("DROP TABLE UTMB")
    conn.sql("CREATE TABLE UTMB AS SELECT * FROM data;")
    return print("data successfully saved to duckDB")


if __name__ == "__main__":
    data_complete = []
    '''
    for p in range(1, 4):  # there are 3 pages with races
        url = f"https://www.finishers.com/en/courses?page={p}&series=utmbevent"
        page = utmb_extract_page(url, local=True)
        data_raw = utmb_extract_data(page)
        data_cleaned = utmb_extract_clean_data(data_raw)
        data_complete.extend(data_cleaned)
        print(len(data_complete))
    '''
    #pd.DataFrame(data_complete).to_csv("data/utmb_data_raw.csv", index=False)
    data_complete = pd.read_csv('data/utmb_data_raw.csv')
    data_cleaned = utmb_transform_data(data_complete)
    data_cleaned.to_csv("data/utmb_data_clean.csv", index=False)
    data_cleaned = pd.read_csv("data/utmb_data_clean.csv")
    load_data_to_db(data_cleaned)
    conn = duckdb.connect("datautmb_db.duckdb")
    data_cleaned = conn.sql("select * from UTMB")
    print(data_cleaned)
    tables = conn.sql("SHOW ALL TABLES")
