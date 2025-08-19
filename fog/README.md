# Camada Fog - Ponte de Protocolos

Este diretório contém os componentes da camada fog que fazem a ponte de protocolos e normalização de dados entre dispositivos de borda e a nuvem.

## Componentes

### Fluxos Node-RED
- **flows.json**: Fluxos pré-configurados para a ponte de protocolos
- **Ponte CoAP para MQTT**: Polls CoAP sensors and publishes to MQTT
- **Ponte HTTP para MQTT**: Accepts HTTP sensor data and forwards to MQTT

### Gateway (Opcional)
- **gateway/**: Diretório para componentes adicionais de gateway, se necessário

## Recursos

### Ponte de Protocolos
- **CoAP → MQTT**: Converte leituras de sensores CoAP em mensagens MQTT
- **HTTP → MQTT**: Aceita chamadas de API REST e publica em MQTT
- **Normalização de Dados**: Garante formato de payload consistente entre protocolos

### Fluxos Node-RED
1. **Fluxo de Polling CoAP**: Solicita periodicamente dados de sensores CoAP
2. **Fluxo de Entrada HTTP**: Aceita requisições POST de sensores HTTP
3. **Fluxo de Processamento de Dados**: Normaliza e valida dados dos sensores
4. **Fluxo de Publicação MQTT**: Publica dados formatados em tópicos MQTT

## Configuração

### Acesso ao Node-RED
- **URL**: http://localhost:1880
- **Usuário**: (nenhum - acesso aberto para desenvolvimento)
- **Fluxos**: Importados automaticamente do flows.json

### Importar Fluxos
1. Abra o Node-RED em http://localhost:1880
2. Vá para Menu → Importar
3. Copie o conteúdo de `flows.json`
4. Clique em Importar

## Descrição dos Fluxos

### Fluxo CoAP para MQTT

```
[Inject Timer] → [CoAP Request] → [Parse JSON] → [Normalize Data] → [MQTT Publish]
      ↓              ↓              ↓              ↓               ↓
   Every 5s      GET /sensor    JSON Parser    Format for     Publish to
                                              MQTT topic    sensors/{type}/{id}
```

**Configuração**:
- **Timer**: Intervalos de 5 segundos
- **CoAP URL**: `coap://host.docker.internal:5683/sensor`
- **Saída**: Múltiplas mensagens MQTT para cada medição

### Fluxo HTTP para MQTT

```
[HTTP Input] → [Validate Data] → [Format Message] → [MQTT Publish] → [HTTP Response]
      ↓              ↓               ↓                ↓                ↓
POST /sensors/   Check required    Add metadata    Publish to      Return 200 OK
{type}/{id}        fields        & timestamp     MQTT topic     or error status
```

**Endpoints**:
- `POST /sensors/temperature/{id}` 
- `POST /sensors/humidity/{id}`
- `POST /sensors/luminosity/{id}`

## Fluxo de Dados

### Formatos de Entrada

#### Resposta CoAP
```json
{
  "sensor_id": "coap-env-001",
  "timestamp": "2024-01-01T12:00:00Z",
  "measurements": {
    "temperature": {"value": 22.1, "unit": "°C"},
    "humidity": {"value": 65.2, "unit": "%"},
    "pressure": {"value": 1013.25, "unit": "hPa"}
  },
  "protocol": "coap",
  "origin": "edge"
}
```

#### Requisição HTTP
```bash
POST /sensors/temperature/temp-002
Content-Type: application/json

{
  "value": 24.1,
  "unit": "°C",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Formato de Saída (MQTT)
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 22.1,
  "unit": "°C",
  "sensor_id": "coap-env-001-temperature",
  "origin": "fog",
  "source_protocol": "coap"
}
```

## Testes

### Testar Ponte CoAP
```bash
# Iniciar sensor CoAP
cd ../edge/coap_simulator
python coap_sensor.py

# Verificar saída de depuração do Node-RED para dados CoAP
# Monitorar MQTT para mensagens ponteadas
mosquitto_sub -h localhost -t "sensors/+/coap-env-001-+"
```

### Testar Ponte HTTP
```bash
# Enviar dados de sensor HTTP
curl -X POST "http://localhost:1880/sensors/temperature/temp-http-001" \
  -H "Content-Type: application/json" \
  -d '{
    "value": 25.5,
    "unit": "°C",
    "timestamp": "2024-01-01T12:00:00Z"
  }'

# Monitorar MQTT para mensagens ponteadas
mosquitto_sub -h localhost -t "sensors/temperature/temp-http-001"
```

### Depuração no Node-RED
1. Abra a interface do Node-RED em http://localhost:1880
2. Ative os nós de depuração nos fluxos
3. Veja as mensagens de depuração no painel direito
4. Monitore o fluxo de dados em cada etapa

## Customização

### Adicionar Suporte a Novo Protocolo
1. Crie um novo fluxo no Node-RED
2. Adicione um nó de entrada para o protocolo (por exemplo, UDP, Serial)
3. Adicione lógica de análise e normalização de dados
4. Conecte ao nó de saída MQTT

### Modificar Processamento de Dados
1. Edite os nós de função "Normalize Data"
2. Adicione lógica de validação
3. Implemente transformações personalizadas
4. Adicione tratamento de erros

### Configurar MQTT
1. Edite as configurações do nó do broker MQTT
2. Atualize os parâmetros de conexão
3. Configure QoS e políticas de retenção
4. Configure autenticação, se necessário

## Configuração dos Fluxos

### Nó Broker MQTT
```javascript
{
  "broker": "mosquitto",
  "port": 1883,
  "clientid": "nodered-bridge",
  "keepalive": 60,
  "cleansession": true
}
```

### Função de Requisição CoAP
```javascript
// Requisição CoAP para sensor ambiental
const coapUrl = "coap://host.docker.internal:5683/sensor";
msg.url = coapUrl;
msg.method = "GET";
return msg;
```

### Função de Normalização de Dados
```javascript
// Converter dados CoAP para formato de sensor MQTT
const coapData = msg.payload;
const messages = [];

for (const [measureType, measurement] of Object.entries(coapData.measurements)) {
  const mqttPayload = {
    ts: coapData.timestamp,
    type: measureType,
    value: measurement.value,
    unit: measurement.unit,
    sensor_id: `${coapData.sensor_id}-${measureType}`,
    origin: "fog",
    source_protocol: "coap"
  };
  
  messages.push({
    topic: `sensors/${measureType}/${mqttPayload.sensor_id}`,
    payload: JSON.stringify(mqttPayload)
  });
}

return messages;
```

## Monitoramento

### Dashboard do Node-RED
- **Status do Fluxo**: Indicação visual dos fluxos ativos
- **Saída de Depuração**: Inspeção em tempo real das mensagens
- **Tratamento de Erros**: Notificações de mensagens com falha

### Monitoramento MQTT
```bash
# Monitorar todas as mensagens ponteadas
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"origin":"fog"'

# Monitorar fontes de protocolo específicas
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"source_protocol":"coap"'
```

### Saúde do Sistema
```bash
# Verificar status do container Node-RED
docker-compose ps node-red

# Ver visualizar logs do Node-RED
docker-compose logs -f node-red

# Verificar conectividade do broker MQTT
mosquitto_pub -h localhost -t "test/nodered" -m "ping"
```

## Solução de Problemas

### Problemas na Ponte CoAP
1. **Sensor CoAP não respondendo**:
   - Verifique se o sensor CoAP está em execução
   - Verifique a conectividade da rede
   - Verifique as configurações do firewall para a porta UDP 5683

2. **Sem saída MQTT**:
   - Verifique a conexão com o broker MQTT
   - Verifique se há erros no nó da função
   - Ative a saída de depuração

### Problemas na Ponte HTTP
1. **Falha nas requisições HTTP**:
   - Verifique a configuração do nó de entrada HTTP do Node-RED
   - Verifique se o formato da requisição corresponde ao esquema esperado
   - Verifique o status da resposta no painel de depuração

2. **Dados não normalizados**:
   - Revise a lógica da função de normalização
   - Verifique se há erros de JavaScript nos nós de função
   - Valide o formato dos dados de entrada

### Problemas Gerais
1. **Fluxos não funcionando**:
   - Reimporte o flows.json
   - Verifique se todos os nós estão devidamente conectados
   - Verifique a configuração do broker MQTT

2. **Problemas de desempenho**:
   - Ajuste os intervalos de polling
   - Verifique os recursos do sistema
   - Monitore o uso de memória do Node-RED

## Integração

### Com a Camada de Borda
- Recebe automaticamente dados de sensores CoAP
- Aceita requisições POST HTTP de sensores
- Faz a ponte entre protocolos de forma transparente

### Com a Camada de Nuvem
- Publica dados normalizados em tópicos MQTT
- Backend da nuvem se inscreve nesses tópicos
- Fornece formato de dados consistente para processamento