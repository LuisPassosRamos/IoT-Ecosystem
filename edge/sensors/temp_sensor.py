import os
import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_ID = "temp-001"
TOPIC = f"sensors/temperature/{SENSOR_ID}"

NORMAL_RANGE = (18.0, 32.0)
ANOMALY_THRESHOLD = 5.0
UPDATE_INTERVAL = 2

class TemperatureSensor:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"sensor-{SENSOR_ID}")
        self.last_value = 22.0
        self.setup_mqtt()
    
    def setup_mqtt(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        else:
            print(f"Failed to connect to MQTT broker: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
    
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
        try:
            result = self.client.publish(TOPIC, json.dumps(payload), qos=1, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "[ANOMALY]" if payload.get("anomaly") else "[NORMAL]"
                print(f"{status} Published: {payload}")
            else:
                print(f"Failed to publish: {result.rc}")
        except Exception as e:
            print(f"Error publishing: {e}")
        self.last_value = value
    
    def run(self):
        try:
            self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            print(f"Temperature sensor {SENSOR_ID} started")
            print(f"Publishing to topic: {TOPIC}")
            print("Press Ctrl+C to stop")
            while True:
                self.publish_reading()
                time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down sensor...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    sensor = TemperatureSensor()
    sensor.run()