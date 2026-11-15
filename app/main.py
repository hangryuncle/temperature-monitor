
from datetime import datetime

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel

from app.database import get_connection
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Measurement(BaseModel):
    id: int
    packet_id: int
    device_id: str
    timestamp: datetime
    rx_timestamp: datetime | None = None
    delay_milliseconds: int | None = None
    temperature: float
    humidity: float
    rssi: int | None = None
    snr: float | None = None


class MeasurementCreate(BaseModel):
    packet_id: int
    device_id: str
    timestamp: datetime
    rx_timestamp: datetime | None = None
    delay_milliseconds: int | None = None
    temperature: float
    humidity: float
    rssi: int | None = None
    snr: float | None = None


@app.get("/")
def home():
    return {"message": "Temperature monitoring API is running!"}


@app.get("/measurements", response_model=list[Measurement])
def get_measurements(
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        device_id: str | None = None
    ):
    if (start_time is None) != (end_time is None):
        raise HTTPException(
            status_code=400,
            detail="Please provide both start_time and end_time"
        )
    if start_time is not None and end_time is not None:
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="start_time must be less than end_time"
            )
        if start_time.tzinfo is None or end_time.tzinfo is None:
            raise HTTPException(
                status_code=400,
                detail="start_time and end_time must be timezone-aware"
        )
    conn = get_connection()

    with conn.cursor() as cur:
        query = """
            SELECT  
                id,
                packet_id,
                device_id,
                timestamp,
                rx_timestamp,
                delay_milliseconds,
                temperature,
                humidity,
                rssi,
                snr
            FROM measurements
            WHERE 1=1
        """

        params = []

        if start_time is not None:
            query += " AND timestamp >= %s"
            params.append(start_time)

            query += " AND timestamp < %s"
            params.append(end_time)

        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)

        query += " ORDER BY timestamp ASC"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        measurements = []

        for row in rows:
            measurements.append(
                Measurement(
                    id=row[0],
                    packet_id=row[1],
                    device_id=row[2],
                    timestamp=row[3],
                    rx_timestamp=row[4],
                    delay_milliseconds=row[5],
                    temperature=row[6],
                    humidity=row[7],
                    rssi=row[8],
                    snr=row[9]
                )
            )
            return measurements


    conn.close()




@app.post("/measurements", response_model=Measurement)
def create_measurement(measurement: MeasurementCreate):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO measurements (
                    packet_id,
                    device_id,
                    timestamp,
                    rx_timestamp,
                    delay_milliseconds,
                    temperature,
                    humidity,
                    rssi,
                    snr
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                measurement.packet_id,
                measurement.device_id,
                measurement.timestamp,
                measurement.rx_timestamp,
                measurement.delay_milliseconds,
                measurement.temperature,
                measurement.humidity,
                measurement.rssi,
                measurement.snr
            ))

            new_id = cur.fetchone()

        conn.commit()
    
        return Measurement(
            id=new_id[0],
            packet_id=measurement.packet_id,
            device_id=measurement.device_id,
            timestamp=measurement.timestamp,
            rx_timestamp=measurement.rx_timestamp,
            delay_milliseconds=measurement.delay_milliseconds,
            temperature=measurement.temperature,
            humidity=measurement.humidity,
            rssi=measurement.rssi,
            snr=measurement.snr
        )
    finally:
        conn.close()


@app.get("/measurements/pdr/{device_id}")
def get_pdr(
    device_id: str,
    start: datetime,
    end: datetime,
    expected_packets: int
):
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT packet_id
            FROM measurements
            WHERE device_id = %s
              AND timestamp >= %s
              AND timestamp < %s
              AND packet_id > 0
            ORDER BY packet_id
        """, (device_id, start, end))

        rows = cur.fetchall()

    conn.close()

    received_ids = [row[0] for row in rows]

    received = len(received_ids)

    expected = expected_packets

    lost = max(expected - received, 0)

    pdr_percent = (
        (received / expected) * 100
        if expected > 0
        else 0
    )

    return {
        "device_id": device_id,
        "start": start,
        "end": end,
        "received": received,
        "expected": expected,
        "lost": lost,
        "pdr_percent": round(pdr_percent, 2),
        "received_packet_ids": received_ids,
    }

