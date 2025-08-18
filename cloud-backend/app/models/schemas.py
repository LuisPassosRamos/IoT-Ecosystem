"""
Pydantic models and database schemas for IoT sensors
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database setup
DATABASE_URL = os.getenv("DB_URL", "sqlite:///data/app.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    sensor_type = Column(String(50), index=True)
    sensor_id = Column(String(100), index=True)
    value = Column(Float)
    unit = Column(String(20))
    origin = Column(String(20))  # edge, fog, cloud
    source_protocol = Column(String(20))  # mqtt, http, coap
    anomaly = Column(Boolean, default=False, index=True)
    raw_data = Column(Text)  # JSON string of original payload

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class SensorReadingBase(BaseModel):
    timestamp: datetime
    sensor_type: str
    sensor_id: str
    value: float
    unit: Optional[str] = None
    origin: str = "edge"
    source_protocol: str = "mqtt"
    anomaly: bool = False

class SensorReadingCreate(SensorReadingBase):
    raw_data: Optional[str] = None

class SensorReadingResponse(SensorReadingBase):
    id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginRequest(BaseModel):
    username: str
    password: str

class SensorLatestResponse(BaseModel):
    sensors: Dict[str, List[SensorReadingResponse]]
    total_count: int
    last_updated: Optional[datetime]

class SensorHistoryResponse(BaseModel):
    readings: List[SensorReadingResponse]
    sensor_id: str
    count: int

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    humidity: float
    pressure: float
    description: str
    timestamp: datetime

class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type: sensor_data, weather_data, alert")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()