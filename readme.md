# UTMB Event Data Pipeline

A data pipeline that extracts and processes race information from all UTMB (Ultra-Trail du Mont-Blanc) World Series events listed on Finishers.com. This pipeline collects comprehensive data about trail running races that are part of the UTMB circuit worldwide.

## Project Overview

This project automatically extracts data about UTMB races from Finishers.com, including:
- Race names and locations
- Race distances and elevation gains
- Event dates and confirmation status
- Race disciplines and styles
- Geographic coordinates
- Event images and links

Technologies used:
- Apache Airflow for workflow orchestration
- Selenium for web scraping
- PostgreSQL for metadata storage
- Redis for task queue management
- Docker for containerization
- DuckDB for data storage and querying

## Project Structure

```
utmb_data_eng/
├── dags/              # Airflow DAG definitions
├── plugins/           # Custom plugins and pipeline code
├── config/           # Configuration files
├── data/            # Data storage
├── tests/           # Test files
├── bash_files/      # Shell scripts
├── logs/            # Log files
└── docker-compose.yaml
```

## Prerequisites

- Docker
- Docker Compose
- Make (optional, for using Makefile commands)

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd utmb_data_eng
```

2. Start the services:
```bash
make start_docker
# or
bash bash_files/start.sh
```

3. Access Airflow UI:
- URL: http://localhost:8080
- Username: airflow
- Password: airflow

4. Run the pipeline:
```bash
make run_dag
```

## Pipeline Components

1. **Extract**: 
   - Scrapes UTMB race data from Finishers.com
   - Navigates through multiple pages of events
   - Handles dynamic content loading using Selenium


2. **Transform**: 
   - Cleans and structures race information
   - Processes distances and creates distance-specific flags
   - Parses dates into start/end dates and duration
   - Extracts race styles and disciplines into separate columns
   - Generates geographic coordinates for race locations

3. **Load**: 
   - Saves processed data to CSV format
   - Stores data in DuckDB for efficient querying
   - Maintains table 'UTMB' with latest race information

## Development

- Install dependencies: `make install`
- Run tests: `make test`
- Format code: `make format`
- Lint code: `make lint`

## Stopping the Services

```bash
make stop_docker
# or
bash bash_files/take_down.sh
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](http://www.apache.org/licenses/LICENSE-2.0) file for details.
