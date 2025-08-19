# Segurança e Proteção de Dados

## Visão Geral

Este documento descreve as medidas de segurança implementadas no IoT Ecosystem e considerações de conformidade com regulações de proteção de dados.

## Arquitetura de Segurança

### Defesa em Profundidade

O Ecossistema IoT implementa múltiplas camadas de segurança:

1. **Segurança do Dispositivo** (Camada de Borda)
2. **Segurança de Rede** (Comunicação)
3. **Segurança de Aplicação** (Nuvem)
4. **Segurança de Dados** (Armazenamento/Transito)
5. **Segurança Operacional** (Monitoramento/Resposta)

## Segurança na Camada de Borda

### Autenticação de Dispositivos
- **Autenticação Baseada em Certificado**: Certificados X.509 para identidade do dispositivo
- **Chaves Pré-compartilhadas (PSK)**: Para dispositivos com recursos limitados
- **Provisionamento de Dispositivos**: Processo seguro de integração

```python
# Exemplo: Cliente MQTT com TLS e certificados
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

### Integridade de Dados dos Sensores
- **Assinaturas Digitais**: Assinatura criptográfica das leituras dos sensores
- **Detecção de Anomalias**: Análise estatística para detectar adulterações
- **Timestamping**: Sincronização segura de tempo (NTP com autenticação)

### Gestão de Dispositivos
- **Atualizações de Firmware**: Atualizações OTA seguras com verificação de assinatura
- **Gestão de Configuração**: Implantação de configuração criptografada
- **Rotação de Chaves**: Gestão automatizada do ciclo de vida de certificados e chaves

## Segurança de Rede

### Segurança na Camada de Transporte

#### Segurança MQTT
```yaml
# Configuração TLS do Mosquitto
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
require_certificate true
use_identity_as_username true
```

#### Segurança HTTP/REST
- **Apenas HTTPS**: Criptografia TLS 1.3 para toda comunicação da API
- **Cabeçalhos HSTS**: Segurança Estrita de Transporte HTTP
- **Pinagem de Certificado**: Fixar certificados em aplicações móveis

#### Segurança CoAP
```python
# CoAP com DTLS
import aiocoap
from aiocoap.credentials import FilesystemCredentials

credentials = FilesystemCredentials("client-cert.pem", "client-key.pem")
protocol = await aiocoap.Context.create_client_context(
    loggername="dtls-client",
    credentials=credentials
)
```

### Segmentação de Rede
- **VLANs**: Redes separadas para dispositivos IoT
- **Regras de Firewall**: Filtragem rigorosa de entrada/saída
- **Acesso VPN**: Acesso remoto seguro para gestão

## Segurança de Aplicação

### Autenticação e Autorização

#### Implementação JWT
```python
# Geração de Token JWT
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# Uso no FastAPI
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
```

#### Controle de Acesso Baseado em Papéis (RBAC)
```python
# Papéis e permissões de usuário
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
                raise HTTPException(status_code=403, detail="Permissões insuficientes")
            return func(current_user)
        return wrapper
    return decorator

@app.get("/v1/sensors/config")
@require_permission("configure")
def get_sensor_config():
    # Apenas administradores podem acessar a configuração do sensor
    pass
```

### Validação e Saneamento de Entrada

#### Modelos Pydantic
```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class SensorReading(BaseModel):
    timestamp: datetime
    sensor_type: str = Field(..., regex="^[a-z_]+$", max_length=50)
    sensor_id: str = Field(..., regex="^[a-zA-Z0-9_-]+$", max_length=100)
    value: float = Field(..., ge=-100, le=1000)  # Faixas de sensor razoáveis
    unit: Optional[str] = Field(None, max_length=20)
    
    @validator('sensor_type')
    def validate_sensor_type(cls, v):
        allowed_types = ['temperature', 'humidity', 'luminosity', 'pressure']
        if v not in allowed_types:
            raise ValueError(f'tipo_sensor deve ser um dos seguintes: {allowed_types}')
        return v

    @validator('value')
    def validate_sensor_value(cls, v, values):
        sensor_type = values.get('sensor_type')
        # Validação específica do tipo
        if sensor_type == 'temperature' and not (-50 <= v <= 100):
            raise ValueError('A temperatura deve estar entre -50°C e 100°C')
        elif sensor_type == 'humidity' and not (0 <= v <= 100):
            raise ValueError('A umidade deve estar entre 0% e 100%')
        return v
```

### Cabeçalhos de Segurança na API
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Middleware de segurança
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

## Segurança de Dados

### Criptografia de Dados

#### Criptografia de Banco de Dados
```python
# SQLAlchemy com campos criptografados
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(100))
    # Criptografar dados sensíveis de localização
    location = Column(EncryptedType(String, secret_key, AesEngine, 'pkcs5'))
    value = Column(Float)
    raw_data = Column(EncryptedType(Text, secret_key, AesEngine, 'pkcs5'))
```

#### Criptografia em Trânsito
- **TLS 1.3**: Todas as comunicações HTTP/MQTT
- **DTLS 1.3**: Comunicações CoAP
- **Criptografia de Ponta a Ponta**: Criptografia opcional de payload para dados sensíveis

### Minimização de Dados
```python
# Políticas de retenção de dados
class DataRetentionPolicy:
    REAL_TIME_RETENTION = timedelta(hours=1)
    DETAILED_RETENTION = timedelta(days=30)
    SUMMARY_RETENTION = timedelta(days=365)
    
    @staticmethod
    def cleanup_old_data():
        # Excluir dados em tempo real com mais de 1 hora
        cutoff = datetime.utcnow() - DataRetentionPolicy.REAL_TIME_RETENTION
        db.query(SensorReading).filter(
            SensorReading.timestamp < cutoff,
            SensorReading.retention_type == "realtime"
        ).delete()
        
        # Agregar dados detalhados em resumos após 30 dias
        # ... implementação
```

## Proteção de Privacidade

### Anonimização de Dados
```python
import hashlib
import hmac

def anonymize_sensor_id(sensor_id: str, salt: str) -> str:
    """Criar identificador de sensor anônimo, mas consistente"""
    return hmac.new(
        salt.encode(), 
        sensor_id.encode(), 
        hashlib.sha256
    ).hexdigest()[:16]

def pseudonymize_location(lat: float, lon: float, precision: int = 3) -> tuple:
    """Reduzir a precisão da localização para proteger a privacidade"""
    return (round(lat, precision), round(lon, precision))
```

### Gestão de Consentimento
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

## Conformidade Regulatória

### GDPR (Regulamento Geral de Proteção de Dados)

#### Implementação dos Direitos do Titular
```python
class GDPRCompliance:
    @staticmethod
    def export_user_data(user_id: str) -> dict:
        """Direito à portabilidade dos dados (Art. 20)"""
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
        """Direito ao apagamento (Art. 17)"""
        # Excluir dados pessoais
        db.query(User).filter(User.id == user_id).delete()
        # Anonimizar dados do sensor em vez de excluir (interesse legítimo)
        db.query(SensorReading).filter(
            SensorReading.user_id == user_id
        ).update({"user_id": None, "anonymized": True})
        db.commit()
    
    @staticmethod
    def rectify_user_data(user_id: str, corrections: dict):
        """Direito à retificação (Art. 16)"""
        user = db.query(User).filter(User.id == user_id).first()
        for field, value in corrections.items():
            if hasattr(user, field):
                setattr(user, field, value)
        db.commit()
```

#### Documentação da Base Legal
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
        # Definir períodos de retenção com base na base legal e propósito
        pass

# Registro de atividades de processamento (Art. 30)
PROCESSING_ACTIVITIES = [
    DataProcessingRecord(
        purpose="Monitoramento ambiental",
        legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
        data_categories=["sensor_readings", "device_identifiers"]
    ),
    DataProcessingRecord(
        purpose="Autenticação de usuário",
        legal_basis=LegalBasis.CONTRACT,
        data_categories=["user_credentials", "session_data"]
    )
]
```

### LGPD (Lei Geral de Proteção de Dados - Brasil)

#### Responsabilidades do Controlador de Dados
```python
class LGPDCompliance:
    @staticmethod
    def generate_privacy_report() -> dict:
        """Gerar avaliações de impacto à privacidade regularmente"""
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
        """Notificação de violação de dados (Art. 48)"""
        incident = DataBreachIncident(
            type=incident_type,
            affected_users=len(affected_users),
            reported_to_authority=False,
            reported_to_users=False,
            timestamp=datetime.utcnow()
        )
        
        # Notificar autoridades dentro de 72 horas se alto risco
        if incident.severity == "high":
            # Implementação para notificação à autoridade
            pass
        
        # Notificar usuários afetados sem demora indevida
        for user_id in affected_users:
            # Implementação para notificação ao usuário
            pass
```

## Monitoramento de Segurança

### Auditoria de Logs
```python
import logging
from functools import wraps

# Logger de eventos de segurança
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
            security_logger.info(f"AÇÃO: {action} | USUÁRIO: {user.username if hasattr(user, 'username') else user} | IP: {request.client.host}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/v1/sensors/config")
@audit_log("atualização_config_sensor")
def update_sensor_config():
    pass
```

### Detecção de Intrusão
```python
from collections import defaultdict, deque
from datetime import datetime, timedelta

class IntrusionDetection:
    def __init__(self):
        self.failed_attempts = defaultdict(deque)
        self.rate_limits = defaultdict(deque)
    
    def check_brute_force(self, ip_address: str) -> bool:
        """Detectar ataques de força bruta"""
        now = datetime.utcnow()
        window = now - timedelta(minutes=15)
        
        # Limpar tentativas antigas
        attempts = self.failed_attempts[ip_address]
        while attempts and attempts[0] < window:
            attempts.popleft()
        
        # Verificar se muitas tentativas falhadas
        if len(attempts) >= 5:
            security_logger.warning(f"FORCA_BRUTA_DETECTADA: {ip_address}")
            return True
        return False
    
    def record_failed_attempt(self, ip_address: str):
        self.failed_attempts[ip_address].append(datetime.utcnow())
    
    def check_rate_limit(self, ip_address: str, limit: int = 100) -> bool:
        """Verificar limite de taxa da API"""
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
    
    # Verificar limite de taxa
    if intrusion_detector.check_rate_limit(ip_address):
        return JSONResponse(
            status_code=429,
            content={"detail": "Limite de taxa excedido"}
        )
    
    response = await call_next(request)
    
    # Registrar tentativas de autenticação falhadas
    if response.status_code == 401:
        intrusion_detector.record_failed_attempt(ip_address)
        
        if intrusion_detector.check_brute_force(ip_address):
            # Poderia implementar bloqueio de IP aqui
            pass
    
    return response
```

## Plano de Resposta a Incidentes

### Classificação de Incidentes de Segurança
1. **Baixo**: Problemas de configuração menores, tentativas de login falhadas
2. **Médio**: Tentativas de acesso não autorizadas, interrupções de serviço
3. **Alto**: Violação de dados, compromissos de sistema
4. **Crítico**: Compromisso completo do sistema, roubo de dados em larga escala

### Procedimentos de Resposta
1. **Detecção**: Alertas de monitoramento automático
2. **Avaliação**: Classificação de severidade e análise de impacto
3. **Contenção**: Isolar sistemas afetados
4. **Erradicação**: Remover ameaças e vulnerabilidades
5. **Recuperação**: Restaurar serviços e monitorar
6. **Lições Aprendidas**: Atualizar medidas de segurança

### Informações de Contato
- **Equipe de Segurança**: security@iot-ecosystem.local
- **Encarregado de Proteção de Dados**: dpo@iot-ecosystem.local
- **Linha Direta de Emergência**: +1-555-SECURITY

## Testes de Segurança

### Testes Automatizados de Segurança
```yaml
# Testes de segurança na pipeline CI/CD
security_tests:
  - name: "Varredura SAST"
    tool: "bandit"
    command: "bandit -r cloud-backend/ -f json"
  
  - name: "Varredura de Dependências"
    tool: "safety"
    command: "safety check --json"
  
  - name: "Varredura de Container"
    tool: "trivy"
    command: "trivy image iot-backend:latest"
  
  - name: "Teste de Segurança da API"
    tool: "zap"
    command: "zap-baseline.py -t http://localhost:8000"
```

### Agenda de Testes de Intrusão
- **Testes Internos**: Varreduras automatizadas mensais
- **Testes Externos**: Avaliação profissional trimestral
- **Exercícios de Red Team**: Teste abrangente anual

Este framework de segurança assegura que o IoT Ecosystem mantenha forte proteção para dados de sensores e privacidade dos usuários, em conformidade com as principais regulações de proteção de dados.