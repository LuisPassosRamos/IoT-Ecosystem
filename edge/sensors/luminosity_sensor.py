import os
import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_ID = "lum-001"
TOPIC = f"sensors/luminosity/{SENSOR_ID}"

NORMAL_RANGE = (100, 2000)
ANOMALY_THRESHOLD = 500
UPDATE_INTERVAL = 4

class LuminositySensor:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"sensor-{SENSOR_ID}")
        self.last_value = 500
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
        current_hour = datetime.now().hour
        if random.random() < 0.08:
            if random.random() < 0.4:
                value = random.uniform(0, 50)
            elif random.random() < 0.7:
                value = random.uniform(3000, 10000)
            else:
                value = self.last_value + random.choice([-1, 1]) * random.uniform(600, 1500)
        else:
            if 6 <= current_hour <= 18:
                base_light = random.uniform(800, 1500)
            elif 19 <= current_hour <= 22:
                base_light = random.uniform(300, 800)
            else:
                base_light = random.uniform(50, 300)
            variation = random.uniform(-100, 100)
            value = max(NORMAL_RANGE[0], min(NORMAL_RANGE[1], base_light + variation))
        value = max(0, value)
        return round(value, 0)
    
    def create_payload(self, value):
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": "luminosity",
            "value": int(value),
            "unit": "lux",
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
            print(f"Luminosity sensor {SENSOR_ID} started")
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
    sensor = LuminositySensor()
    sensor.run()