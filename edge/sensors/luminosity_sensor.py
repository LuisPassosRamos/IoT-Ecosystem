#!/usr/bin/env python3
"""
Luminosity sensor simulator with anomaly detection.
Publishes to MQTT topic: sensors/luminosity/lum-001
"""

import os
import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_ID = "lum-001"
TOPIC = f"sensors/luminosity/{SENSOR_ID}"

# Sensor parameters
NORMAL_RANGE = (100, 2000)  # Normal luminosity range in lux
ANOMALY_THRESHOLD = 500  # Luminosity jump threshold for anomaly
UPDATE_INTERVAL = 4  # seconds

class LuminositySensor:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"sensor-{SENSOR_ID}")
        self.last_value = 500  # Start with moderate luminosity
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client"""
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
        """Detect luminosity anomalies"""
        anomaly = False
        
        # Check if value is outside normal range
        if value < NORMAL_RANGE[0] or value > NORMAL_RANGE[1]:
            anomaly = True
        
        # Check for sudden jumps
        if abs(value - self.last_value) > ANOMALY_THRESHOLD:
            anomaly = True
            
        return anomaly
    
    def generate_reading(self):
        """Generate luminosity reading with occasional anomalies"""
        # Simulate day/night cycle and lighting conditions
        current_hour = datetime.now().hour
        
        # 92% normal readings, 8% anomalous
        if random.random() < 0.08:
            # Generate anomalous reading
            if random.random() < 0.4:
                # Very dark (equipment failure, power outage)
                value = random.uniform(0, 50)
            elif random.random() < 0.7:
                # Very bright (direct sunlight, artificial lighting malfunction)
                value = random.uniform(3000, 10000)
            else:
                # Sudden jump (light switching, curtains)
                value = self.last_value + random.choice([-1, 1]) * random.uniform(600, 1500)
        else:
            # Normal reading based on time of day
            if 6 <= current_hour <= 18:  # Daytime
                base_light = random.uniform(800, 1500)
            elif 19 <= current_hour <= 22:  # Evening
                base_light = random.uniform(300, 800)
            else:  # Night
                base_light = random.uniform(50, 300)
            
            # Add small variation
            variation = random.uniform(-100, 100)
            value = max(NORMAL_RANGE[0], min(NORMAL_RANGE[1], 
                       base_light + variation))
        
        # Ensure luminosity is positive
        value = max(0, value)
        return round(value, 0)
    
    def create_payload(self, value):
        """Create sensor payload"""
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": "luminosity",
            "value": int(value),
            "unit": "lux",
            "sensor_id": SENSOR_ID,
            "origin": "edge"
        }
        
        # Add anomaly flag if detected
        if self.detect_anomaly(value):
            payload["anomaly"] = True
            
        return payload
    
    def publish_reading(self):
        """Generate and publish a sensor reading"""
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
        """Run the sensor simulation"""
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