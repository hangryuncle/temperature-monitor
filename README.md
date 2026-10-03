# Temperature Monitor

A lightweight Python FastAPI service for collecting and querying temperature and humidity sensor readings from connected devices.

This project exposes a REST API for storing measurement records in PostgreSQL and retrieving recent readings or packet delivery statistics for individual devices.

## Features

- FastAPI-based REST API
- PostgreSQL integration via `psycopg`
- Store temperature, humidity, RSSI, SNR, and timing metadata
- Query all recorded measurements
- Calculate packet delivery ratio (PDR) per device
- Environment-variable based configuration

## Tech Stack

- Python 3
- FastAPI
- Uvicorn
- PostgreSQL
- python-dotenv

## Project Structure

```text
.
├── app/
│   ├── __init__.py
│   ├── database.py
│   └── main.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- PostgreSQL database
- Access to a configured `DATABASE_URL`

## Installation

1. Clone the repository
2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your database connection string:

```env
DATABASE_URL=postgresql://username:password@host:5432/temperature_monitor
```

## Running the API

Start the application with:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

## API Endpoints

### GET /

Returns a basic health/status message.

Example response:

```json
{
  "message": "Temperature monitoring API is running!"
}
```

### GET /measurements

Returns all measurements ordered by timestamp in descending order.

### POST /measurements

Creates a new measurement record.

Example request body:

```json
{
  "packet_id": 42,
  "device_id": "sensor-01",
  "timestamp": "2026-01-15T12:30:00",
  "temperature": 21.8,
  "humidity": 46.2,
  "rssi": -67,
  "snr": 18.5
}
```

### GET /measurements/pdr/{device_id}

Returns packet delivery ratio statistics for a specific device.

Example response:

```json
{
  "device_id": "sensor-01",
  "received": 120,
  "expected": 150,
  "lost": 30,
  "pdr_percent": 80.0
}
```

## Data Model

The application expects a PostgreSQL `measurements` table with fields like:

- `id`
- `packet_id`
- `device_id`
- `timestamp`
- `temperature`
- `humidity`
- `rssi`
- `snr`

Example SQL schema:

```sql
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    packet_id INT NOT NULL,
    device_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    rssi INT,
    snr DOUBLE PRECISION
);
```

## Notes

- The project currently expects the database to already exist and be accessible via the `DATABASE_URL` environment variable.
- There are no migration scripts in the repository at this time, so the database schema should be created manually or managed externally.

## License

No license file is included in the repository, so usage and distribution rights are not explicitly defined.
