import os
import time
import json
import random
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_ID = "temp-001"
TOPIC = f"sensors/temperature/{SENSOR_ID}"

NORMAL_RANGE = (18.0, 32.0)
ANOMALY_THRESHOLD = 5.0
UPDATE_INTERVAL = 2
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TemperatureSensor:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"sensor-{SENSOR_ID}")
        self.last_value = 22.0
        self.is_connected = False
        self.reconnect_attempts = 0
        self.setup_mqtt()
    
    def setup_mqtt(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        logger.warning("Disconnected from MQTT broker")
        
    def connect_with_retry(self):
        """Attempt to connect to MQTT broker with retry logic"""
        while self.reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            try:
                logger.info(f"Attempting to connect to MQTT broker (attempt {self.reconnect_attempts + 1}/{MAX_RECONNECT_ATTEMPTS})")
                self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
                self.client.loop_start()
                return True
            except Exception as e:
                self.reconnect_attempts += 1
                logger.error(f"Connection attempt {self.reconnect_attempts} failed: {e}")
                if self.reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
                    logger.info(f"Retrying in {RECONNECT_DELAY} seconds...")
                    time.sleep(RECONNECT_DELAY)
        
        logger.error("Max reconnection attempts reached. Unable to connect to MQTT broker.")
        return False
    
    def detect_anomaly(self, value):
        anomaly = False
        if value < NORMAL_RANGE[0] or value > NORMAL_RANGE[1]:
            anomaly = True
        if abs(value - self.last_value) > ANOMALY_THRESHOLD:
            anomaly = True
        return anomaly
    
    def generate_reading(self):
        if random.random() < 0.05:
            if random.random() < 0.5:
                value = random.choice([
                    random.uniform(-5.0, 10.0),
                    random.uniform(40.0, 50.0)
                ])
            else:
                value = self.last_value + random.choice([-1, 1]) * random.uniform(6.0, 10.0)
        else:
            variation = random.uniform(-1.0, 1.0)
            value = max(NORMAL_RANGE[0], min(NORMAL_RANGE[1], self.last_value + variation))
        return round(value, 2)
    
    def create_payload(self, value):
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": "temperature",
            "value": value,
            "unit": "°C",
            "sensor_id": SENSOR_ID,
            "origin": "edge"
        }
        if self.detect_anomaly(value):
            payload["anomaly"] = True
        return payload
    
    def publish_reading(self):
        value = self.generate_reading()
        payload = self.create_payload(value)
        
        # Check connection status
        if not self.is_connected:
            logger.warning("MQTT client not connected. Attempting to reconnect...")
            if not self.connect_with_retry():
                logger.error("Unable to reconnect. Skipping this reading.")
                return
        
        try:
            result = self.client.publish(TOPIC, json.dumps(payload), qos=1, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "[ANOMALY]" if payload.get("anomaly") else "[NORMAL]"
                logger.info(f"{status} Published: {json.dumps(payload)}")
            else:
                logger.error(f"Failed to publish: {result.rc}")
        except Exception as e:
            logger.error(f"Error publishing: {e}")
            self.is_connected = False
        self.last_value = value
    
    def run(self):
        try:
            logger.info(f"Starting temperature sensor {SENSOR_ID}")
            logger.info(f"Target MQTT broker: {MQTT_HOST}:{MQTT_PORT}")
            logger.info(f"Publishing to topic: {TOPIC}")
            
            if not self.connect_with_retry():
                logger.error("Failed to establish initial connection. Exiting.")
                return
                
            logger.info("Temperature sensor started successfully")
            logger.info("Press Ctrl+C to stop")
            
            while True:
                self.publish_reading()
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Shutting down sensor...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            if self.is_connected:
                self.client.loop_stop()
                self.client.disconnect()
            logger.info("Temperature sensor stopped")

if __name__ == "__main__":
    sensor = TemperatureSensor()
    sensor.run()