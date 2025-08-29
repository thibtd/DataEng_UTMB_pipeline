from geopy.geocoders import Nominatim
import re, datetime
import pandas as pd
import wordninja


def round_to_nearest_5(x: float) -> float:
    x: float = float(x)
    return round(x / 5) * 5


def get_lat_long(place: str) -> tuple:
    geolocator = Nominatim(user_agent="utmb_pipeline", timeout=40)
    location = geolocator.geocode(place)
    return location.latitude, location.longitude


def clean_dates(row: pd.Series) -> tuple:
    # Data for Mozart race is wrong and the data structure is different from everything else
    # thus here is a dirty patch for it
    multidays: bool = None
    start_day: int = None
    end_day: int = None
    month: int = None
    year: int = None
    duration: int = None
    if "Mozart" in row["name"] and "2025" in row["date"]:
        multidays = False
        start_day = 7
        end_day = 7
        month = datetime.datetime.strptime("June", "%B").month
        year = 2025
        duration = 1
    elif row["date_confirmed"]:
        if "➜" in row["date"]:
            splits: list = row["date"].split("➜")
            start_split: list[str] = splits[0].strip()
            end_split: list[str] = splits[1].strip().replace(",", "")

            multidays = True

            try:  # Pattern : DD day -> Month DD YYYY
                start_day = int(start_split.split(" ")[0])
                month_name = end_split.split(" ")[0]
                month = datetime.datetime.strptime(month_name, "%B").month
                end_day = int(end_split.split(" ")[1])
                year = int(end_split.split(" ")[2])
            except ValueError:  # Pattern: Day, Mth DD -> Day Mth DD YYYY
                start_day = int(start_split.split(" ")[2])
                month_name = start_split.split(" ")[1]
                month = datetime.datetime.strptime(month_name, "%b").month
                end_day = int(end_split.split(" ")[2])
                year = int(end_split.split(" ")[3])
            start_date = datetime.datetime(year, month, start_day)
            end_date = datetime.datetime(year, month, end_day)
            duration = (end_date - start_date).days
        else:
            multidays = False
            splits: list = row["date"].replace(",", "").split(" ")
            start_day = int(splits[2])
            end_day = int(splits[2])
            month_name: str = splits[1]
            month = datetime.datetime.strptime(month_name, "%B").month
            year = int(splits[3])
            duration = 1
    else:
        month_reg = r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\b"
        dates: list = re.search(month_reg, row["date"]).group(0).split(" ")
        month_name: str = dates[0]
        month = datetime.datetime.strptime(month_name, "%B").month
        year = int(dates[1])
    return multidays, start_day, end_day, month, year, duration


# Function to retrieve offered distances for a row
def get_offered_X(row: pd.Series, prefix: str, prefix_sep: str = "_") -> str:
    cols_name = prefix + prefix_sep
    if prefix_sep in prefix:
        cols_name = prefix
    # Filter columns that start with 'X'
    distance_columns = [col for col in row.index if col.startswith(cols_name)]

    # Extract columns where the flag is True
    offered_distances = [
        col.replace(cols_name, "") for col in distance_columns if row[col]
    ]

    # Join the distances into a comma-separated string
    return ", ".join(offered_distances)


def split_into_words(input_string):
    replacements = {"S": "Sand", "U": "UTMB"}
    remove = ["and", "TMB"]
    # Use wordninja to split the string
    words = wordninja.split(input_string)
    words = [replacements.get(word, word) for word in words]
    words = [word for word in words if word not in remove]
    return " ".join(words)
