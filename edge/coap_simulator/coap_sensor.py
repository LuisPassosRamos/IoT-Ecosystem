import asyncio
import json
import random
import time
from datetime import datetime
import logging
import os
import aiocoap.resource as resource
import aiocoap

# On Windows, aiocoap fails when binding to any-address (0.0.0.0).
# Make host configurable and default to localhost.
COAP_HOST = os.getenv("COAP_HOST", "127.0.0.1")
COAP_PORT = int(os.getenv("COAP_PORT", "5683"))
SENSOR_ID = "coap-env-001"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentalSensorResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.last_temp = 21.0
        self.last_humidity = 60.0
        self.last_pressure = 1013.25
    
    def generate_sensor_data(self):
        temp_variation = random.uniform(-0.5, 0.5)
        self.last_temp = max(18.0, min(30.0, self.last_temp + temp_variation))
        hum_variation = random.uniform(-2.0, 2.0)
        self.last_humidity = max(40.0, min(70.0, self.last_humidity + hum_variation))
        pressure_variation = random.uniform(-0.5, 0.5)
        self.last_pressure = max(995.0, min(1025.0, self.last_pressure + pressure_variation))
        anomaly = random.random() < 0.05
        data = {
            "sensor_id": SENSOR_ID,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "measurements": {
                "temperature": {
                    "value": round(self.last_temp, 2),
                    "unit": "°C"
                },
                "humidity": {
                    "value": round(self.last_humidity, 1),
                    "unit": "%"
                },
                "pressure": {
                    "value": round(self.last_pressure, 2),
                    "unit": "hPa"
                }
            },
            "protocol": "coap",
            "origin": "edge"
        }
        if anomaly:
            data["anomaly"] = True
            if random.random() < 0.33:
                data["measurements"]["temperature"]["value"] = random.choice([5.0, 45.0])
            elif random.random() < 0.5:
                data["measurements"]["humidity"]["value"] = random.choice([10.0, 95.0])
            else:
                data["measurements"]["pressure"]["value"] = random.choice([980.0, 1040.0])
        return data
    
    async def render_get(self, request):
        try:
            sensor_data = self.generate_sensor_data()
            payload = json.dumps(sensor_data).encode('utf-8')
            logger.info(f"CoAP request served: {sensor_data}")
            return aiocoap.Message(
                code=aiocoap.CONTENT,
                payload=payload,
                content_format=aiocoap.numbers.media_types_rev['application/json']
            )
        except Exception as e:
            logger.error(f"Error serving CoAP request: {e}")
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR)

class TemperatureResource(resource.Resource):
    async def render_get(self, request):
        temp_data = {
            "sensor_id": f"{SENSOR_ID}-temp",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "temperature",
            "value": round(random.uniform(18.0, 30.0), 2),
            "unit": "°C",
            "protocol": "coap",
            "origin": "edge"
        }
        payload = json.dumps(temp_data).encode('utf-8')
        logger.info(f"Temperature CoAP request: {temp_data}")
        return aiocoap.Message(
            code=aiocoap.CONTENT,
            payload=payload,
            content_format=aiocoap.numbers.media_types_rev['application/json']
        )

async def main():
    root = resource.Site()
    root.add_resource(['sensor'], EnvironmentalSensorResource())
    root.add_resource(['temperature'], TemperatureResource())
    context = await aiocoap.Context.create_server_context(root, bind=(COAP_HOST, COAP_PORT))
    logger.info(f"CoAP sensor server started on {COAP_HOST}:{COAP_PORT}")
    logger.info("Available resources:")
    logger.info("  coap://localhost:5683/sensor - Full environmental data")
    logger.info("  coap://localhost:5683/temperature - Temperature only")
    logger.info("Press Ctrl+C to stop")
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down CoAP server...")
    finally:
        await context.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCoAP sensor stopped")