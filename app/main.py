from datetime import datetime

from fastapi import FastAPI
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
    temperature: float
    humidity: float
    rssi: int | None = None
    snr: float | None = None    

class MeasurementCreate(BaseModel):
    packet_id: int
    device_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    rssi: int | None = None
    snr: float | None = None

@app.get("/")
def home():
    return {"message": "Temperature monitoring API is running!"}


@app.get("/measurements", response_model=list[Measurement])
def get_measurements():
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, packet_id,device_id, timestamp, temperature, humidity, rssi, snr
            FROM measurements
            ORDER BY timestamp DESC
        """)

        rows = cur.fetchall()

    conn.close()

    measurements = []

    for row in rows:
        measurements.append(
            Measurement(
                id=row[0],
                packet_id=row[1],
                device_id=row[2],
                timestamp=row[3],
                temperature=row[4],
                humidity=row[5],
                rssi=row[6],
                snr=row[7]
            )
        )

    return measurements
@app.post("/measurements", response_model=Measurement)
def create_measurement(measurement: MeasurementCreate):
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO measurements (packet_id, device_id, timestamp, temperature, humidity, rssi, snr)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (measurement.packet_id, measurement.device_id, measurement.timestamp, measurement.temperature, measurement.humidity,measurement.rssi, measurement.snr),)

        new_id = cur.fetchone()

    conn.commit()
    conn.close()

    return Measurement(
            id=new_id[0],
            packet_id=measurement.packet_id,
            device_id=measurement.device_id,
            timestamp=measurement.timestamp,
            temperature=measurement.temperature,            
            humidity=measurement.humidity,
            rssi=measurement.rssi,
            snr=measurement.snr
        )

@app.get("/measurements/pdr/{device_id}")
def get_pdr(device_id: str):
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) AS received,
                MAX(packet_id) AS expected
            FROM measurements
            WHERE device_id = %s
              AND packet_id > 0
        """, (device_id,))

        row = cur.fetchone()

    conn.close()

    received = row[0]
    expected = row[1] or 0
    lost = expected - received

    pdr_percent = (
        (received / expected) * 100
        if expected > 0
        else 0
    )

    return {
        "device_id": device_id,
        "received": received,
        "expected": expected,
        "lost": lost,
        "pdr_percent": round(pdr_percent, 2),
        }
