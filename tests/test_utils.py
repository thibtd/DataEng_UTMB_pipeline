import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd

from plugins.utils import (
    round_to_nearest_5,
    get_lat_long,
    clean_dates,
    get_offered_X,
    split_into_words,
)


def test_round_to_nearest_5():
    assert round_to_nearest_5(7) == 5
    assert round_to_nearest_5(8) == 10
    assert round_to_nearest_5(12) == 10
    assert round_to_nearest_5(13) == 15
    assert round_to_nearest_5(0) == 0
    assert round_to_nearest_5(2.4) == 0
    assert round_to_nearest_5(2.6) == 5
    assert round_to_nearest_5(-7) == -5
    assert round_to_nearest_5(-8) == -10


def test_get_lat_long():
    # Test with a known location
    lat, lon = get_lat_long("Paris, France")
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert round(lat) == 49
    assert round(lon) == 2

    # Test with another known location
    lat, lon = get_lat_long("New York, USA")
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert round(lat) == 41
    assert round(lon) == -74

    # Test error handling for invalid location
    with pytest.raises(AttributeError):
        get_lat_long("ThisIsNotARealPlace12345")


def test_clean_dates():
    # Test Mozart special case
    row = pd.Series({"name": "Mozart Race", "date": "2025", "date_confirmed": False})
    multidays, start_day, end_day, month, year, duration = clean_dates(row)
    assert multidays == False
    assert start_day == 7
    assert end_day == 7
    assert month == 6  # June
    assert year == 2025
    assert duration == 1

    # Test multi-day event with arrow
    row = pd.Series(
        {
            "name": "multi-day event",
            "date": "1 ➜ August 5, 2024",
            "date_confirmed": True,
        }
    )
    multidays, start_day, end_day, month, year, duration = clean_dates(row)
    assert multidays == True
    assert start_day == 1
    assert end_day == 5
    assert month == 8  # August
    assert year == 2024
    assert duration == 4

    # Test single day event
    row = pd.Series(
        {
            "name": "Single day event",
            "date": "Friday, June 15, 2024",
            "date_confirmed": True,
        }
    )
    multidays, start_day, end_day, month, year, duration = clean_dates(row)
    assert multidays == False
    assert start_day == 15
    assert end_day == 15
    assert month == 6  # June
    assert year == 2024
    assert duration == 1

    # Test unconfirmed date
    row = pd.Series(
        {
            "name": "Unconfirmed date",
            "date": "Race in September 2024",
            "date_confirmed": False,
        }
    )
    multidays, start_day, end_day, month, year, duration = clean_dates(row)
    assert month == 9  # September
    assert year == 2024


def test_get_offered_X():
    # Test with default separator
    row = pd.Series({"X_100": True, "X_50": False, "X_20": True, "other": True})
    assert get_offered_X(row, "X") == "100, 20"

    # Test with custom separator
    row = pd.Series(
        {"dist-100": True, "dist-50": True, "dist-20": False, "other": True}
    )
    assert get_offered_X(row, "dist", "-") == "100, 50"

    # Test with separator in prefix
    row = pd.Series(
        {"race_X_100": True, "race_X_50": False, "race_X_20": True, "other": True}
    )
    assert get_offered_X(row, "race_X_") == "100, 20"

    # Test with empty result
    row = pd.Series({"X_100": False, "X_50": False, "other": True})
    assert get_offered_X(row, "X") == ""

    def test_split_into_words():
        # Test basic string splitting
        assert split_into_words("helloworld") == "hello world"

        # Test replacement of 'S' with 'Sand'
        assert split_into_words("desertS") == "desert Sand"

        # Test replacement of 'U' with 'UTMB'
        assert split_into_words("U100") == "UTMB 100"

        # Test removal of 'and' and 'TMB'
        assert split_into_words("TMBrace") == "race"
        assert split_into_words("runandrace") == "run race"

        # Test multiple replacements and removals
        assert split_into_words("UTMBandSdesert") == "UTMB Sand desert"

        # Test empty string
        assert split_into_words("") == ""
