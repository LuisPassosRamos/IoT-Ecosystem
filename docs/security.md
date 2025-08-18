# Security and LGPD Compliance

## Security Overview

The IoT-Ecosystem implements multi-layered security controls across all system components to protect data integrity, confidentiality, and availability while ensuring compliance with data protection regulations.

## Authentication & Authorization

### JWT-Based Authentication

**Implementation**: JSON Web Tokens (JWT) with HS256 signing
```javascript
// Token Structure
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "admin",           // Subject (username)
    "iat": 1640995200,        // Issued at (timestamp)
    "exp": 1641081600,        // Expiration (timestamp)
    "type": "access_token"    // Token type
  }
}
```

**Security Features**:
- ✅ Configurable expiration (default: 24 hours)
- ✅ Secret key rotation capability
- ✅ Stateless token validation
- ✅ Standard JWT claims for interoperability

**Configuration**:
```bash
# Environment Variables
JWT_SECRET=your-secure-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Demo User Management

**Current Implementation**: Single demo user for proof-of-concept
```bash
DEMO_USERNAME=admin
DEMO_PASSWORD=password123
```

**Production Recommendations**:
- ✅ Integrate with enterprise identity providers (LDAP, Active Directory)
- ✅ Implement role-based access control (RBAC)
- ✅ Add multi-factor authentication (MFA)
- ✅ Use secure password hashing (bcrypt, Argon2)
- ✅ Implement account lockout and rate limiting

### API Endpoint Protection

**Protected Endpoints**:
```python
# Requires valid JWT token
GET /v1/auth/verify          # Token verification
GET /v1/auth/user-info       # User information
POST /v1/auth/logout         # Logout
GET /v1/auth/protected       # Demo protected route

# Public Endpoints (no authentication required)
POST /v1/auth/login          # User login
GET /health                  # Health check
GET /                        # API information
```

## Network Security

### Transport Layer Security

**HTTPS/TLS**:
```nginx
# Production NGINX Configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
}
```

**MQTT Security**:
```conf
# Mosquitto TLS Configuration
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
tls_version tlsv1.2
```

**WebSocket Security**:
```javascript
// Secure WebSocket Connection
const ws = new WebSocket('wss://yourdomain.com/ws', {
    headers: {
        'Authorization': `Bearer ${jwt_token}`
    }
});
```

### Network Segmentation

**Docker Network Isolation**:
```yaml
networks:
  iot-internal:
    driver: bridge
    internal: true
  iot-external:
    driver: bridge
```

**Firewall Rules** (Production):
```bash
# Allow only necessary ports
iptables -A INPUT -p tcp --dport 443 -j ACCEPT   # HTTPS
iptables -A INPUT -p tcp --dport 8883 -j ACCEPT  # MQTT TLS
iptables -A INPUT -p tcp --dport 1880 -j ACCEPT  # Node-RED (internal only)
iptables -A INPUT -j DROP                        # Default deny
```

## Data Security

### Data at Rest

**Database Security**:
```python
# SQLite with encryption (production)
DATABASE_URL = "sqlite+pysqlcipher://:password@/path/to/encrypted.db"

# Connection security
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None
    }
)
```

**File System Protection**:
```bash
# Restrict file permissions
chmod 600 /app/data/sensor_data.db
chmod 700 /app/data/
chown app:app /app/data/
```

### Data in Transit

**MQTT Message Encryption**:
```python
# TLS Configuration for MQTT Client
import ssl

client = mqtt.Client()
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED

client.tls_set_context(context)
client.connect("mqtt.example.com", 8883, 60)
```

**API Request Encryption**:
```python
# FastAPI with HTTPS enforcement
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

## Input Validation & Sanitization

### Pydantic Data Validation

**Sensor Data Validation**:
```python
from pydantic import BaseModel, Field, validator

class SensorReading(BaseModel):
    ts: str = Field(..., regex=r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')
    type: str = Field(..., regex=r'^(temperature|humidity|luminosity)$')
    value: float = Field(..., ge=-50, le=100)
    unit: str = Field(..., max_length=20)
    sensor_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=50)
    
    @validator('ts')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid timestamp format')
```

**SQL Injection Prevention**:
```python
# Using SQLAlchemy ORM (parameterized queries)
from sqlalchemy.orm import Session

def get_sensor_data(db: Session, sensor_id: str, limit: int):
    return db.query(SensorData)\
             .filter(SensorData.sensor_id == sensor_id)\
             .limit(limit)\
             .all()
```

### CORS Configuration

**Cross-Origin Resource Sharing**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Production: specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## LGPD Compliance (Lei Geral de Proteção de Dados)

### Data Protection Principles

**1. Data Minimization**
```python
# Collect only necessary data
class SensorReading(BaseModel):
    # No personal identifiers
    sensor_id: str          # Anonymous device ID
    timestamp: datetime     # Required for time series
    value: float           # Sensor measurement only
    # No location, IP addresses, or personal data
```

**2. Purpose Limitation**
```python
# Data Processing Purpose Declaration
DATA_PROCESSING_PURPOSES = {
    "environmental_monitoring": "Collect environmental data for monitoring",
    "anomaly_detection": "Detect unusual sensor readings for safety",
    "system_health": "Monitor system performance and availability"
}
```

**3. Data Retention**
```python
# Automatic Data Retention
class DataRetentionService:
    def cleanup_old_data(self):
        cutoff_date = datetime.utcnow() - timedelta(days=365)  # 1 year retention
        
        # Delete old sensor readings
        db.query(SensorReading)\
          .filter(SensorReading.timestamp < cutoff_date)\
          .delete()
        
        # Log retention action
        logger.info(f"Deleted sensor data older than {cutoff_date}")
```

### Data Subject Rights

**Right to Access**:
```python
@app.get("/v1/data/export")
async def export_user_data(user_id: str = Depends(get_current_user)):
    """Export all data associated with the user."""
    data = {
        "user_info": get_user_info(user_id),
        "sensor_data": get_user_sensor_data(user_id),
        "system_logs": get_user_system_logs(user_id)
    }
    return data
```

**Right to Deletion**:
```python
@app.delete("/v1/data/user/{user_id}")
async def delete_user_data(user_id: str = Depends(admin_required)):
    """Delete all data associated with a user."""
    delete_user_sensor_data(user_id)
    delete_user_system_logs(user_id)
    delete_user_account(user_id)
    
    logger.info(f"Deleted all data for user {user_id}")
    return {"message": "User data deleted successfully"}
```

**Right to Rectification**:
```python
@app.put("/v1/data/sensor/{reading_id}")
async def update_sensor_reading(
    reading_id: int,
    updated_data: SensorReading,
    user: dict = Depends(get_current_user)
):
    """Update incorrect sensor reading."""
    reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
    
    # Audit trail
    audit_log = AuditLog(
        action="data_correction",
        user_id=user["sub"],
        resource_id=reading_id,
        old_value=reading.value,
        new_value=updated_data.value,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
```

### Privacy by Design

**Data Anonymization**:
```python
import hashlib

def anonymize_sensor_id(original_id: str, salt: str) -> str:
    """Create anonymous sensor identifier."""
    return hashlib.sha256((original_id + salt).encode()).hexdigest()[:16]

def anonymize_ip_address(ip: str) -> str:
    """Anonymize IP address (last octet)."""
    parts = ip.split('.')
    if len(parts) == 4:
        parts[-1] = '0'  # Remove last octet
    return '.'.join(parts)
```

**Consent Management**:
```python
class ConsentRecord(BaseModel):
    user_id: str
    purpose: str
    granted_at: datetime
    expires_at: Optional[datetime]
    withdrawn_at: Optional[datetime]

@app.post("/v1/consent")
async def record_consent(consent: ConsentRecord):
    """Record user consent for data processing."""
    db.add(consent)
    db.commit()
    
    logger.info(f"Consent recorded for user {consent.user_id}, purpose: {consent.purpose}")
```

### Audit and Compliance

**Audit Logging**:
```python
class AuditLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests for audit purposes."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log audit record
    audit_record = AuditLog(
        user_id=get_user_from_request(request),
        action=f"{request.method} {request.url.path}",
        resource_type="api_endpoint",
        resource_id=str(request.url),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )
    
    save_audit_log(audit_record)
    return response
```

**Data Processing Register**:
```yaml
# LGPD Data Processing Register
data_processing_activities:
  - name: "Environmental Monitoring"
    purpose: "Monitor environmental conditions"
    legal_basis: "Legitimate interest"
    data_categories: ["sensor_readings", "timestamps"]
    retention_period: "1 year"
    security_measures: ["encryption", "access_control", "audit_logs"]
    
  - name: "System Health Monitoring"
    purpose: "Ensure system availability and performance"
    legal_basis: "Legitimate interest"
    data_categories: ["system_logs", "performance_metrics"]
    retention_period: "6 months"
    security_measures: ["log_rotation", "access_control"]
```

## Security Monitoring

### Intrusion Detection

**Log Analysis**:
```python
import re
from collections import defaultdict

class SecurityMonitor:
    def __init__(self):
        self.failed_logins = defaultdict(int)
        self.suspicious_patterns = [
            r'(union|select|insert|drop|delete).*(from|into)',  # SQL injection
            r'<script.*?>.*?</script>',                         # XSS attempts
            r'\.\./',                                           # Path traversal
        ]
    
    def analyze_request(self, request_data: str, ip: str) -> bool:
        """Analyze request for suspicious patterns."""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                self.log_security_event("suspicious_pattern", ip, pattern)
                return True
        return False
    
    def check_rate_limit(self, ip: str, endpoint: str) -> bool:
        """Check if IP exceeds rate limits."""
        # Implementation for rate limiting
        pass
```

**Alert System**:
```python
class SecurityAlerts:
    @staticmethod
    async def send_security_alert(event_type: str, details: dict):
        """Send security alert via multiple channels."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": "high",
            "details": details
        }
        
        # Send to monitoring system
        await send_to_monitoring(alert)
        
        # Send to admin email (if configured)
        if os.getenv("ADMIN_EMAIL"):
            await send_email_alert(alert)
        
        # Send to Slack/Teams (if configured)
        if os.getenv("SLACK_WEBHOOK"):
            await send_slack_alert(alert)
```

## Security Best Practices

### Development Security

**Secure Configuration**:
```python
# Security Headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

**Environment Security**:
```bash
# Secure environment variables
export JWT_SECRET=$(openssl rand -base64 32)
export DATABASE_ENCRYPTION_KEY=$(openssl rand -base64 32)
export ADMIN_EMAIL="security@yourdomain.com"

# File permissions
chmod 400 .env
chmod 600 ssl/private.key
chmod 644 ssl/certificate.crt
```

### Deployment Security

**Container Security**:
```dockerfile
# Use non-root user
FROM python:3.11-slim
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Security scanning
RUN apt-get update && apt-get install -y --no-install-recommends \
    security-updates && \
    rm -rf /var/lib/apt/lists/*

# Read-only filesystem
VOLUME ["/tmp", "/var/tmp"]
```

**Secrets Management**:
```yaml
# Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: iot-secrets
type: Opaque
stringData:
  jwt-secret: "your-jwt-secret"
  db-password: "your-db-password"
  openweather-api-key: "your-api-key"
```

### Incident Response

**Security Incident Playbook**:

1. **Detection**: Automated monitoring alerts or manual discovery
2. **Containment**: Isolate affected systems, revoke compromised tokens
3. **Investigation**: Analyze logs, determine scope and impact
4. **Recovery**: Restore services, patch vulnerabilities
5. **Lessons Learned**: Update security measures, improve monitoring

**Emergency Procedures**:
```bash
# Emergency shutdown
docker-compose down
systemctl stop iot-ecosystem

# Token revocation
python3 -c "
import os
from app.auth import revoke_all_tokens
revoke_all_tokens()
print('All tokens revoked')
"

# Database backup
cp sensor_data.db sensor_data.backup.$(date +%Y%m%d_%H%M%S)
```

This security framework provides comprehensive protection while ensuring LGPD compliance through privacy-by-design principles, data minimization, and robust audit capabilities.