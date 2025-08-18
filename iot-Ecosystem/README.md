# IoT-Ecosystem

Minimal, modular IoT environment monitoring stack: Edge (sensors), Fog (Node-RED), Cloud (FastAPI), MQTT broker, and a realtime frontend with Chart.js. Uses SQLite by default. Intentional simplicity.

Quick start
- Copy .env.example to .env and adjust settings (optional).
- Start services: `./scripts/start-local.sh` (Linux/macOS) or `docker-compose up --build`.
- Open:
  - Backend API/Docs: http://localhost:8000/docs
  - Frontend UI: http://localhost:8000/ui
  - Node-RED: http://localhost:1880
  - MQTT: 1883 (TCP), 9001 (WebSocket)

Run sensors locally
- `pip install paho-mqtt aiocoap` (for CoAP simulator).
- Set `MQTT_HOST=localhost` when running outside Docker.
- Example: `python edge/sensors/temp_sensor.py`

What it does
- Edge publishes MQTT telemetry to `sensors/<type>/<id>` with ISO8601 UTC timestamps and basic anomaly detection.
- Fog (Node-RED) can bridge CoAP → MQTT and normalize JSON.
- Cloud backend subscribes to MQTT, persists readings in SQLite, provides REST endpoints, WebSocket live stream, JWT login, and an OpenWeather proxy.
- Frontend shows 3 charts (temperature, humidity, luminosity) and flags large deviations vs. forecast.

Useful commands
- Start: `docker-compose up --build`
- Stop: `docker-compose down`
- Tests: `pip install -r cloud-backend/requirements.txt pytest && pytest`

Notes
- Default demo user: from .env.example (do not use in production).
- For MySQL, set `DB_URL` accordingly and run your own DB (not included).
