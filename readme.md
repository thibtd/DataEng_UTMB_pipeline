[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://utmb-recommender.streamlit.app) [![Make test](https://github.com/thibtd/DataEng_UTMB_pipeline/actions/workflows/main.yml/badge.svg)](https://github.com/thibtd/DataEng_UTMB_pipeline/actions/workflows/main.yml) [![update data](https://github.com/thibtd/DataEng_UTMB_pipeline/actions/workflows/dataPipeline.yml/badge.svg)](https://github.com/thibtd/DataEng_UTMB_pipeline/actions/workflows/dataPipeline.yml)

# UTMB Event Data Pipeline & Recommender System

A comprehensive system that extracts race information from UTMB (Ultra-Trail du Mont-Blanc) World Series events and provides personalized race recommendations.

## Live Demo

**The application is live!** Access the deployed recommender system on Streamlit Cloud:
[https://utmb-recommender.streamlit.app](https://utmb-recommender.streamlit.app)

## Project Overview

This project consists of two main components:
1. A data pipeline that automatically extracts data from Finishers.com
2. A recommender system with an interactive web interface for personalized race suggestions

## Data Pipeline

![Data Pipeline Schema](assets/schema.png)

The data pipeline extracts race information from UTMB World Series events on a monthly schedule using GitHub Actions. It processes the data through several transformation steps and loads it into both CSV and DuckDB storage formats. The pipeline runs automatically on the 18th of each month to ensure up-to-date race information.

### Pipeline Steps:
1. Web scraping using Selenium to extract UTMB race data
2. Data cleaning and transformation
3. Geo-location enrichment
4. Storage in DuckDB and CSV formats
5. Automatic data updates via GitHub Actions

## Recommender System

The project includes a machine learning-based recommendation engine that helps users find UTMB races matching their preferences:

- Uses K-means clustering to group similar races
- Provides similarity-based recommendations
- Includes feature importance explanations for recommendations
- Visualizes race information on interactive maps

### Features:
- Automated data extraction from UTMB World Series events retrieved on finishers.com
- Machine learning-based race recommendations
- Interactive web interface for exploring races
- Visualization of race locations and characteristics
- Customizable search based on user preferences
- Explainable recommendations with feature correlation plots

## Technologies Used:
- Apache Airflow for workflow orchestration
- Selenium for web scraping
- DuckDB for data storage
- Streamlit for web interface
- Scikit-learn for machine learning
- Folium for interactive maps
- LIME for model explanations
- Docker for containerization
- GitHub Actions for CI/CD and scheduled data updates

## Project Structure
```
utmb_data_eng/
├── dags/              # Airflow DAG definitions
├── plugins/           # Custom plugins and pipeline code
│   ├── recommender.py # Race recommendation system
│   └── utils.py      # Utility functions
├── app.py            # Streamlit web application
├── config/           # Configuration files
├── data/            # Data storage
├── tests/           # Test files
├── bash_files/      # Shell scripts
├── logs/            # Log files
└── docker-compose.yaml
```

## Deployment Options

### 1. Use the Live Deployment

The easiest way to use this application is through our Streamlit Cloud deployment:
[https://utmb-recommender.streamlit.app](https://utmb-recommender.streamlit.app)

### 2. Local Deployment

#### Prerequisites

- Docker
- Docker Compose
- Make (optional, for using Makefile commands)

#### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/thibtd/DataEng_UTMB_pipeline.git
cd DataEng_UTMB_pipeline
```
2. Start the services:
```
make start_docker
# or
bash bash_files/start.sh
```
3. Access Airflow UI:
URL: http://localhost:8080
Username: airflow
Password: airflow

4. Run the pipeline:
``` 
make run_dag 
```
5. Access the Streamlit app:
```
streamlit run app.py 
```

## CI/CD Pipeline
This project includes GitHub Actions workflows for:

Automated testing of code changes
Monthly data pipeline execution (on the 18th of each month)
Automatic data updates committed back to the repository

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

