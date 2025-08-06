import os, sys
from unittest import mock

import test

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from IPython import embed
import pytest
from bs4 import BeautifulSoup
import pandas as pd
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import TimeoutException
import numpy as np
from plugins.utmb_pipeline import (
    utmb_extract_page,
    utmb_transform_data,
    utmb_extract_data,
    utmb_extract_clean_data,
    load_data_to_db,
)


@pytest.fixture
def mock_webdriver():
    with patch("plugins.utmb_pipeline.webdriver") as mock:
        mock.Chrome.return_value = MagicMock()
        mock.Remote.return_value = MagicMock()
        yield mock


def test_utmb_extract_page_local(mock_webdriver):
    # Test local driver
    url = "https://test.com"
    mock_driver = mock_webdriver.Chrome.return_value
    mock_driver.page_source = "<html>test content</html>"

    result = utmb_extract_page(url, local=True)

    assert mock_webdriver.Chrome.called
    assert not mock_webdriver.Remote.called
    mock_driver.get.assert_called_with(url)  # Fixed assertion
    assert result == "<html>test content</html>"
    assert mock_driver.quit.called


def test_utmb_extract_page_remote(mock_webdriver):
    # Test remote driver
    url = "https://test.com"
    mock_driver = mock_webdriver.Remote.return_value
    mock_driver.page_source = "<html>test content</html>"

    result = utmb_extract_page(url, local=False)

    assert mock_webdriver.Remote.called
    assert not mock_webdriver.Chrome.called
    mock_driver.get.assert_called_with(url)  # Fixed assertion
    assert result == "<html>test content</html>"
    assert mock_driver.quit.called


def test_utmb_extract_page_timeout(mock_webdriver):
    # Test timeout exception handling
    url = "https://test.com"
    mock_driver = mock_webdriver.Chrome.return_value
    mock_driver.page_source = "<html>test content</html>"
    mock_driver.until.side_effect = TimeoutException()

    result = utmb_extract_page(url, local=True)

    assert result == "<html>test content</html>"
    assert mock_driver.quit.called


def test_utmb_transform_data():
    # Create sample input data
    sample_data = [
        {
            "name": "Test Event by UTMB®",
            "distances": "50 km100 km ",
            "date": "20 Thu ➜ March 21, 2025Date confirmed",
            "date_confirmed": True,
            "country": "France",
            "city": "Paris",
            "styles": "Trail Running⛰️ +2",
            "discipline": "Running +1",
            "image": "/image.jpg",
            "link": "https://test.com",
        }
    ]

    with patch("plugins.utmb_pipeline.get_lat_long") as mock_geo:
        mock_geo.return_value = (48.8566, 2.3522)

        result = utmb_transform_data(sample_data)

        # Test name cleaning
        assert "by UTMB®" not in result["name"].iloc[0]

        # Test distances transformation
        assert "distance_50" in result.columns
        assert "distance_100" in result.columns
        assert result["distance_50"].iloc[0] == True
        assert result["distance_100"].iloc[0] == True

        # Test styles transformation
        assert "style_TrailRunning" in result.columns
        assert result["style_TrailRunning"].iloc[0] == True

        # Test discipline transformation
        assert "discipline_Running" in result.columns
        assert result["discipline_Running"].iloc[0] == True

        # Test date transformation
        assert "multidays" in result.columns
        assert "start_day" in result.columns
        assert "end_day" in result.columns
        assert "month" in result.columns
        assert "year" in result.columns
        assert "duration" in result.columns

        # Test geolocation
        assert "latitude" in result.columns
        assert "longitude" in result.columns
        assert result["latitude"].iloc[0] == 48.8566
        assert result["longitude"].iloc[0] == 2.3522

        # Test dropped columns
        assert "distances" not in result.columns
        assert "styles" not in result.columns
        assert "discipline" not in result.columns
        assert "date" not in result.columns


def test_utmb_extract_data():
    # Test with sample HTML containing multiple events
    sample_html = """
        <html>
            <a class="style_EventPreview__kWm7L group no-link-underline">Event 1</a>
            <a class="style_EventPreview__kWm7L group no-link-underline">Event 2</a>
            <a class="style_EventPreview__kWm7L group no-link-underline">Event 3</a>
            <div>Some other content</div>
        </html>
    """
    events = utmb_extract_data(sample_html)
    assert len(events) == 3
    assert all(event.name == "a" for event in events)
    assert all("style_EventPreview__kWm7L" in event["class"] for event in events)

    # Test with HTML containing no events
    empty_html = "<html><div>No events here</div></html>"
    events = utmb_extract_data(empty_html)
    assert len(events) == 0

    # Test with invalid HTML
    invalid_html = "Not valid HTML"
    events = utmb_extract_data(invalid_html)
    assert len(events) == 0


def test_load_data_to_db(tmp_path):
    # Create test data
    mock_embeddings = [1*384]  # Mock embedding vector
    test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"],"embeddings": [mock_embeddings, mock_embeddings, mock_embeddings]})
    # Mock duckdb connection and operations
    with patch("plugins.utmb_pipeline.duckdb") as mock_duckdb:
        mock_conn = MagicMock()
        mock_duckdb.connect.return_value = mock_conn

        # Mock show tables query - case 1: table doesn't exist
        mock_conn.sql.return_value.df.return_value = pd.DataFrame({"name": []})
        load_data_to_db(test_data)

        # Verify connection was created with correct path
        mock_duckdb.connect.assert_called_once_with("data/utmb_db.duckdb")

        # Case 2: table exists
        mock_conn.reset_mock()
        mock_conn.sql.return_value.df.return_value = pd.DataFrame({"name": ["UTMB"]})
        load_data_to_db(test_data)


def test_utmb_extract_clean_data():
    # Create sample BeautifulSoup HTML elements
    sample_html = """
        <a class="style_EventPreview__kWm7L group no-link-underline" href="/test">
            <div class="typo-h4 leading-tight mb-1">Test Event</div>
            <div class="styles_Distances__GLSe1">100 km</div>
            <div class="flex flex-row items-center style_Date__UbJPv py-1">March 21, 2025</div>
            <span class="styles_Chip__5DJ6w styles_Confirmed__talWF">Confirmed</span>
            <div class="style_City__mrIOD"><img title="France"/>Paris</div>
            <div class="style_Tags__1wVj6 nice-scrollbar">Trail Running</div>
            <div class="style_Disciplines__KoinH">Running</div>
            <div class="imgage"> <img src="/image.jpg"/> </div>
        </a>
    """
    soup = BeautifulSoup(sample_html, "html.parser")
    events = soup.find_all(
        "a", {"class": "style_EventPreview__kWm7L group no-link-underline"}
    )

    result = utmb_extract_clean_data(events)

    assert len(result) == 1
    event = result[0]

    # Test all fields are extracted correctly
    assert event["name"] == "Test Event"
    assert event["distances"] == "100 km"
    assert event["date"] == "March 21, 2025"
    assert event["date_confirmed"] == True
    assert event["country"] == "France"
    assert event["city"] == "Paris"
    assert event["styles"] == "Trail Running"
    assert event["discipline"] == "Running"
    assert event["link"] == "https://www.finishers.com/test"

    # Test with missing optional elements
    sample_html_missing = """
        <a class="style_EventPreview__kWm7L group no-link-underline" href="/test">
            <div class="typo-h4 leading-tight mb-1">Test Event</div>
            <div class="styles_Distances__GLSe1">100 km</div>
            <div class="flex flex-row items-center style_Date__UbJPv py-1">March 21, 2025</div>
            <div class="style_City__mrIOD">
                <img title="France"/>
                Paris
            </div>
            <div class="style_Tags__1wVj6 nice-scrollbar">Trail Running</div>
            <div class="style_Disciplines__KoinH">Running</div>
        </a>
    """
    soup = BeautifulSoup(sample_html_missing, "html.parser")
    events = soup.find_all(
        "a", {"class": "style_EventPreview__kWm7L group no-link-underline"}
    )

    result = utmb_extract_clean_data(events)
    event = result[0]

    # Test handling of missing elements
    assert event["date_confirmed"] == False
    assert event["image"] == None
