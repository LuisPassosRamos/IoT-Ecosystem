# Security and Data Protection

## Overview

This document outlines the security measures implemented in the IoT Ecosystem and compliance considerations for data protection regulations.

## Security Architecture

### Defense in Depth

The IoT Ecosystem implements multiple layers of security:

1. **Device Security** (Edge Layer)
2. **Network Security** (Communication)
3. **Application Security** (Fog/Cloud)
4. **Data Security** (Storage/Transit)
5. **Operational Security** (Monitoring/Response)

## Edge Layer Security

### Device Authentication
- **Certificate-based Authentication**: X.509 certificates for device identity
- **Pre-shared Keys (PSK)**: For resource-constrained devices
- **Device Provisioning**: Secure onboarding process

```python
# Example: MQTT client with TLS and certificates
import ssl
import paho.mqtt.client as mqtt

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_cert_chain("client-cert.pem", "client-key.pem")
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED

client = mqtt.Client()
client.tls_set_context(context)
client.connect("mqtt.iot-ecosystem.local", 8883, 60)
```

### Sensor Data Integrity
- **Digital Signatures**: Cryptographic signing of sensor readings
- **Anomaly Detection**: Statistical analysis to detect tampering
- **Timestamping**: Secure time synchronization (NTP with authentication)

### Device Management
- **Firmware Updates**: Secure OTA updates with signature verification
- **Configuration Management**: Encrypted configuration deployment
- **Key Rotation**: Automated certificate and key lifecycle management

## Network Security

### Transport Layer Security

#### MQTT Security
```yaml
# Mosquitto TLS Configuration
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
require_certificate true
use_identity_as_username true
```

#### HTTP/REST Security
- **HTTPS Only**: TLS 1.3 encryption for all API communication
- **HSTS Headers**: HTTP Strict Transport Security
- **Certificate Pinning**: Pin certificates in mobile applications

#### CoAP Security
```python
# CoAP with DTLS
import aiocoap
from aiocoap.credentials import FilesystemCredentials

credentials = FilesystemCredentials("client-cert.pem", "client-key.pem")
protocol = await aiocoap.Context.create_client_context(
    loggername="dtls-client",
    credentials=credentials
)
```

### Network Segmentation
- **VLANs**: Separate networks for IoT devices
- **Firewall Rules**: Strict ingress/egress filtering
- **VPN Access**: Secure remote access for management

## Application Security

### Authentication and Authorization

#### JWT Implementation
```python
# JWT Token Generation
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# Usage in FastAPI
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### Role-Based Access Control (RBAC)
```python
# User roles and permissions
class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"  
    VIEWER = "viewer"

PERMISSIONS = {
    UserRole.ADMIN: ["read", "write", "delete", "configure"],
    UserRole.OPERATOR: ["read", "write"],
    UserRole.VIEWER: ["read"]
}

def require_permission(permission: str):
    def decorator(func):
        def wrapper(current_user: User = Depends(get_current_user)):
            user_permissions = PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return func(current_user)
        return wrapper
    return decorator

@app.get("/v1/sensors/config")
@require_permission("configure")
def get_sensor_config():
    # Only admins can access sensor configuration
    pass
```

### Input Validation and Sanitization

#### Pydantic Models
```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class SensorReading(BaseModel):
    timestamp: datetime
    sensor_type: str = Field(..., regex="^[a-z_]+$", max_length=50)
    sensor_id: str = Field(..., regex="^[a-zA-Z0-9_-]+$", max_length=100)
    value: float = Field(..., ge=-100, le=1000)  # Reasonable sensor ranges
    unit: Optional[str] = Field(None, max_length=20)
    
    @validator('sensor_type')
    def validate_sensor_type(cls, v):
        allowed_types = ['temperature', 'humidity', 'luminosity', 'pressure']
        if v not in allowed_types:
            raise ValueError(f'sensor_type must be one of {allowed_types}')
        return v

    @validator('value')
    def validate_sensor_value(cls, v, values):
        sensor_type = values.get('sensor_type')
        # Type-specific validation
        if sensor_type == 'temperature' and not (-50 <= v <= 100):
            raise ValueError('Temperature must be between -50°C and 100°C')
        elif sensor_type == 'humidity' and not (0 <= v <= 100):
            raise ValueError('Humidity must be between 0% and 100%')
        return v
```

### API Security Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["iot-ecosystem.local", "*.iot-ecosystem.local"])
app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Data Security

### Data Encryption

#### Database Encryption
```python
# SQLAlchemy with encrypted fields
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(100))
    # Encrypt sensitive location data
    location = Column(EncryptedType(String, secret_key, AesEngine, 'pkcs5'))
    value = Column(Float)
    raw_data = Column(EncryptedType(Text, secret_key, AesEngine, 'pkcs5'))
```

#### Transit Encryption
- **TLS 1.3**: All HTTP/MQTT communications
- **DTLS 1.3**: CoAP communications
- **End-to-End Encryption**: Optional payload encryption for sensitive data

### Data Minimization
```python
# Data retention policies
class DataRetentionPolicy:
    REAL_TIME_RETENTION = timedelta(hours=1)
    DETAILED_RETENTION = timedelta(days=30)
    SUMMARY_RETENTION = timedelta(days=365)
    
    @staticmethod
    def cleanup_old_data():
        # Delete real-time data older than 1 hour
        cutoff = datetime.utcnow() - DataRetentionPolicy.REAL_TIME_RETENTION
        db.query(SensorReading).filter(
            SensorReading.timestamp < cutoff,
            SensorReading.retention_type == "realtime"
        ).delete()
        
        # Aggregate detailed data to summaries after 30 days
        # ... implementation
```

## Privacy Protection

### Data Anonymization
```python
import hashlib
import hmac

def anonymize_sensor_id(sensor_id: str, salt: str) -> str:
    """Create anonymous but consistent sensor identifier"""
    return hmac.new(
        salt.encode(), 
        sensor_id.encode(), 
        hashlib.sha256
    ).hexdigest()[:16]

def pseudonymize_location(lat: float, lon: float, precision: int = 3) -> tuple:
    """Reduce location precision to protect privacy"""
    return (round(lat, precision), round(lon, precision))
```

### Consent Management
```python
class ConsentManager:
    @staticmethod
    def record_consent(user_id: str, purpose: str, granted: bool):
        consent = UserConsent(
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host
        )
        db.add(consent)
        db.commit()
    
    @staticmethod
    def check_consent(user_id: str, purpose: str) -> bool:
        consent = db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.purpose == purpose
        ).order_by(UserConsent.timestamp.desc()).first()
        
        return consent and consent.granted
```

## Regulatory Compliance

### GDPR (General Data Protection Regulation)

#### Data Subject Rights Implementation
```python
class GDPRCompliance:
    @staticmethod
    def export_user_data(user_id: str) -> dict:
        """Right to data portability (Art. 20)"""
        user_data = {
            "user_info": db.query(User).filter(User.id == user_id).first(),
            "sensor_readings": db.query(SensorReading).filter(
                SensorReading.user_id == user_id
            ).all(),
            "consent_history": db.query(UserConsent).filter(
                UserConsent.user_id == user_id
            ).all()
        }
        return user_data
    
    @staticmethod
    def delete_user_data(user_id: str):
        """Right to erasure (Art. 17)"""
        # Delete personal data
        db.query(User).filter(User.id == user_id).delete()
        # Anonymize sensor data instead of deleting (legitimate interest)
        db.query(SensorReading).filter(
            SensorReading.user_id == user_id
        ).update({"user_id": None, "anonymized": True})
        db.commit()
    
    @staticmethod
    def rectify_user_data(user_id: str, corrections: dict):
        """Right to rectification (Art. 16)"""
        user = db.query(User).filter(User.id == user_id).first()
        for field, value in corrections.items():
            if hasattr(user, field):
                setattr(user, field, value)
        db.commit()
```

#### Legal Basis Documentation
```python
class LegalBasis:
    CONSENT = "consent"  # Art. 6(1)(a)
    CONTRACT = "contract"  # Art. 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Art. 6(1)(c)
    VITAL_INTERESTS = "vital_interests"  # Art. 6(1)(d)
    PUBLIC_TASK = "public_task"  # Art. 6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Art. 6(1)(f)

class DataProcessingRecord:
    def __init__(self, purpose: str, legal_basis: str, data_categories: list):
        self.purpose = purpose
        self.legal_basis = legal_basis
        self.data_categories = data_categories
        self.retention_period = self.calculate_retention()
        
    def calculate_retention(self):
        # Define retention periods based on legal basis and purpose
        pass

# Record of processing activities (Art. 30)
PROCESSING_ACTIVITIES = [
    DataProcessingRecord(
        purpose="Environmental monitoring",
        legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
        data_categories=["sensor_readings", "device_identifiers"]
    ),
    DataProcessingRecord(
        purpose="User authentication",
        legal_basis=LegalBasis.CONTRACT,
        data_categories=["user_credentials", "session_data"]
    )
]
```

### LGPD (Lei Geral de Proteção de Dados - Brazil)

#### Data Controller Responsibilities
```python
class LGPDCompliance:
    @staticmethod
    def generate_privacy_report() -> dict:
        """Generate regular privacy impact assessments"""
        return {
            "data_types_processed": ["environmental_sensors", "user_auth"],
            "processing_purposes": ["monitoring", "analytics", "alerts"],
            "data_sharing": "none",
            "security_measures": ["encryption", "access_controls", "audit_logs"],
            "data_retention": "automated_deletion_after_retention_period",
            "user_rights_requests": db.query(UserRightsRequest).count()
        }
    
    @staticmethod
    def incident_response(incident_type: str, affected_users: list):
        """Data breach notification (Art. 48)"""
        incident = DataBreachIncident(
            type=incident_type,
            affected_users=len(affected_users),
            reported_to_authority=False,
            reported_to_users=False,
            timestamp=datetime.utcnow()
        )
        
        # Notify authorities within 72 hours if high risk
        if incident.severity == "high":
            # Implementation for authority notification
            pass
        
        # Notify affected users without undue delay
        for user_id in affected_users:
            # Implementation for user notification
            pass
```

## Security Monitoring

### Audit Logging
```python
import logging
from functools import wraps

# Security event logger
security_logger = logging.getLogger("security")
security_handler = logging.FileHandler("security.log")
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)

def audit_log(action: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or 'anonymous'
            security_logger.info(f"ACTION: {action} | USER: {user.username if hasattr(user, 'username') else user} | IP: {request.client.host}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/v1/sensors/config")
@audit_log("sensor_config_update")
def update_sensor_config():
    pass
```

### Intrusion Detection
```python
from collections import defaultdict, deque
from datetime import datetime, timedelta

class IntrusionDetection:
    def __init__(self):
        self.failed_attempts = defaultdict(deque)
        self.rate_limits = defaultdict(deque)
    
    def check_brute_force(self, ip_address: str) -> bool:
        """Detect brute force attacks"""
        now = datetime.utcnow()
        window = now - timedelta(minutes=15)
        
        # Clean old attempts
        attempts = self.failed_attempts[ip_address]
        while attempts and attempts[0] < window:
            attempts.popleft()
        
        # Check if too many failed attempts
        if len(attempts) >= 5:
            security_logger.warning(f"BRUTE_FORCE_DETECTED: {ip_address}")
            return True
        return False
    
    def record_failed_attempt(self, ip_address: str):
        self.failed_attempts[ip_address].append(datetime.utcnow())
    
    def check_rate_limit(self, ip_address: str, limit: int = 100) -> bool:
        """Check API rate limiting"""
        now = datetime.utcnow()
        window = now - timedelta(minutes=1)
        
        requests = self.rate_limits[ip_address]
        while requests and requests[0] < window:
            requests.popleft()
        
        if len(requests) >= limit:
            return True
        
        requests.append(now)
        return False

intrusion_detector = IntrusionDetection()

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    ip_address = request.client.host
    
    # Check rate limiting
    if intrusion_detector.check_rate_limit(ip_address):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    response = await call_next(request)
    
    # Record failed auth attempts
    if response.status_code == 401:
        intrusion_detector.record_failed_attempt(ip_address)
        
        if intrusion_detector.check_brute_force(ip_address):
            # Could implement IP blocking here
            pass
    
    return response
```

## Incident Response Plan

### Security Incident Classification
1. **Low**: Minor configuration issues, failed login attempts
2. **Medium**: Unauthorized access attempts, service disruptions
3. **High**: Data breaches, system compromises
4. **Critical**: Complete system compromise, large-scale data theft

### Response Procedures
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Severity classification and impact analysis
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and vulnerabilities
5. **Recovery**: Restore services and monitor
6. **Lessons Learned**: Update security measures

### Contact Information
- **Security Team**: security@iot-ecosystem.local
- **Data Protection Officer**: dpo@iot-ecosystem.local
- **Emergency Hotline**: +1-555-SECURITY

## Security Testing

### Automated Security Testing
```yaml
# Security testing in CI/CD pipeline
security_tests:
  - name: "SAST Scan"
    tool: "bandit"
    command: "bandit -r cloud-backend/ -f json"
  
  - name: "Dependency Scan"
    tool: "safety"
    command: "safety check --json"
  
  - name: "Container Scan"
    tool: "trivy"
    command: "trivy image iot-backend:latest"
  
  - name: "API Security Test"
    tool: "zap"
    command: "zap-baseline.py -t http://localhost:8000"
```

### Penetration Testing Schedule
- **Internal Testing**: Monthly automated scans
- **External Testing**: Quarterly professional assessment
- **Red Team Exercises**: Annual comprehensive testing

This security framework ensures the IoT Ecosystem maintains strong protection for sensor data and user privacy while complying with major data protection regulations.