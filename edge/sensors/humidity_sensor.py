import os
import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_ID = "hum-001"
TOPIC = f"sensors/humidity/{SENSOR_ID}"

NORMAL_RANGE = (30.0, 80.0)
ANOMALY_THRESHOLD = 15.0
UPDATE_INTERVAL = 3

class HumiditySensor:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"sensor-{SENSOR_ID}")
        self.last_value = 55.0
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
        if random.random() < 0.07:
            if random.random() < 0.6:
                value = random.choice([
                    random.uniform(5.0, 25.0),
                    random.uniform(85.0, 100.0)
                ])
            else:
                value = self.last_value + random.choice([-1, 1]) * random.uniform(16.0, 25.0)
        else:
            variation = random.uniform(-3.0, 3.0)
            value = max(NORMAL_RANGE[0], min(NORMAL_RANGE[1], self.last_value + variation))
        value = max(0.0, min(100.0, value))
        return round(value, 1)
    
    def create_payload(self, value):
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": "humidity",
            "value": value,
            "unit": "%",
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
            print(f"Humidity sensor {SENSOR_ID} started")
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
    sensor = HumiditySensor()
    sensor.run()