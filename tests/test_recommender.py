import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from plugins.recommender import Recommender


# Fixture to create sample event data with the necessary columns
@pytest.fixture
def sample_data():
    data = pd.DataFrame(
        {
            "month": [6, 7, 8, 9, 10, 11, 6, 7, 8, 9, 10, 11],
            "year": [
                2023,
                2023,
                2023,
                2024,
                2024,
                2024,
                2023,
                2023,
                2023,
                2024,
                2024,
                2024,
            ],
            "start_day": [1, 2, 3, 23, 15, 7, 10, 12, 20, 5, 8, 16],
            "end_day": [10, 11, 12, 23, 18, 9, 15, 14, 25, 7, 10, 20],
            "duration": [5.0, 7.0, 10.0, 1.0, 3.0, 2.0, 5.0, 2.0, 5.0, 2.0, 2.0, 4.0],
            "multidays": [
                True,
                True,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                False,
                True,
            ],
            "latitude": [
                45.0,
                46.0,
                47.0,
                46.0,
                45.5,
                46.5,
                47.5,
                45.2,
                46.8,
                47.2,
                45.8,
                46.2,
            ],
            "longitude": [7.0, 8.0, 9.0, 8.0, 7.5, 8.5, 9.5, 7.2, 8.8, 9.2, 7.8, 8.2],
            "name": [
                "Event1",
                "Event2",
                "Event3",
                "Event4",
                "Event5",
                "Event6",
                "Event7",
                "Event8",
                "Event9",
                "Event10",
                "Event11",
                "Event12",
            ],
            "country": ["Austria"] * 12,
            "city": [f"City{i}" for i in range(1, 13)],
            "image": [f"img{i}" for i in range(1, 13)],
            "link": [f"link{i}" for i in range(1, 13)],
            "date_confirmed": [True] * 12,
            "style_UTMBWorldSeries": [i % 2 == 0 for i in range(12)],
        }
    )
    return data


# Fixture to create a Recommender instance
@pytest.fixture
def recommender(sample_data):
    return Recommender(sample_data)


def test_preprocess(recommender):
    """
    Test that the preprocess method drops the unnecessary columns.
    """
    cleaned = recommender.cleaned_data
    # Columns that should be removed after preprocessing
    dropped_cols = [
        "name",
        "country",
        "city",
        "image",
        "link",
        "date_confirmed",
        "style_UTMBWorldSeries",
        "start_day",
        "end_day",
    ]
    for col in dropped_cols:
        assert col not in cleaned.columns, f"Column '{col}' was not dropped."


def test_process_input(recommender):
    """
    Test that process_input returns a DataFrame with the correct columns.
    """
    preferences = {
        "distance": [10, 30],
        "style": ["Mountain"],
        "month": 6,
        "year": 2023,
        "country": "Austria",
        "multidays": True,
        "disipline": ["Trail"],
    }
    user_input = recommender.process_input(preferences)
    # Check that the returned DataFrame contains exactly the same columns as cleaned_data
    assert isinstance(user_input, pd.DataFrame)
    assert set(user_input.columns) == set(recommender.cleaned_data.columns)


def test_recommend(recommender):
    """
    Test that the recommend method returns a DataFrame with at most top_n recommendations.
    """
    preferences = {
        "distance": [10, 30],
        "style": ["Mountain"],
        "month": 6,
        "year": 2023,
        "country": "Austria",
        "multidays": True,
        "disipline": ["Trail"],
    }
    # Request only 2 recommendations
    recommendations = recommender.recommend(preferences, top_n=2)
    assert isinstance(recommendations, pd.DataFrame)
    assert len(recommendations) <= 2


def test_explain_recommendations(recommender):
    """
    Test that explain_recommendations returns a non-empty Series with feature correlation values.
    """
    preferences = {
        "distance": [10, 30],
        "style": ["Mountain"],
        "month": 6,
        "year": 2023,
        "country": "Austria",
        "multidays": True,
        "disipline": ["Trail"],
    }
    # First run recommendation to populate the .recommended attribute
    recommender.recommend(preferences, top_n=2)
    explanation = recommender.explain_recommendations()
    assert isinstance(explanation, pd.Series)
    # assert not explanation.empty
