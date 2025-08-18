#!/usr/bin/env python3
"""
Luminosity sensor simulator with anomaly detection.
Publishes data to MQTT broker with configurable thresholds.
"""

import os
import time
import json
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LuminositySensor:
    def __init__(self):
        # MQTT Configuration
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic = "sensors/luminosity/sim001"
        
        # Sensor configuration
        self.sensor_id = "luminosity_sim_001"
        self.min_lux = float(os.getenv("LUMINOSITY_MIN", "0.0"))
        self.max_lux = float(os.getenv("LUMINOSITY_MAX", "1000.0"))
        self.jump_threshold = float(os.getenv("LUMINOSITY_JUMP_THRESHOLD", "200.0"))
        
        # State tracking for anomaly detection
        self.last_value: Optional[float] = None
        self.anomaly_probability = 0.03  # 3% chance of anomaly
        
        # MQTT Client
        self.client = mqtt.Client(client_id=f"luminosity-sensor-{self.sensor_id}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        logger.debug(f"Message published with mid: {mid}")
    
    def detect_anomaly(self, value: float) -> bool:
        """Detect anomalies based on range and sudden jumps."""
        anomaly = False
        
        # Range-based anomaly
        if value < self.min_lux or value > self.max_lux:
            anomaly = True
            logger.warning(f"Range anomaly detected: {value} lux (valid range: {self.min_lux}-{self.max_lux} lux)")
        
        # Jump-based anomaly
        if self.last_value is not None:
            jump = abs(value - self.last_value)
            if jump > self.jump_threshold:
                anomaly = True
                logger.warning(f"Jump anomaly detected: {jump} lux change from {self.last_value} lux to {value} lux")
        
        return anomaly
    
    def generate_luminosity(self) -> float:
        """Generate luminosity reading with occasional anomalies."""
        if random.random() < self.anomaly_probability:
            # Generate anomalous reading
            if random.choice([True, False]):
                # Out of range anomaly
                return round(random.choice([
                    random.uniform(-50, self.min_lux - 1),                    # Negative/invalid
                    random.uniform(self.max_lux + 50, self.max_lux + 500)     # Too bright
                ]), 2)
            else:
                # Jump anomaly (if we have previous value)
                if self.last_value is not None:
                    jump_direction = random.choice([-1, 1])
                    jump_size = random.uniform(self.jump_threshold + 50, self.jump_threshold + 200)
                    new_value = self.last_value + (jump_direction * jump_size)
                    return round(max(0, new_value), 2)
        
        # Normal reading - simulate day/night cycle
        current_hour = datetime.now().hour
        
        if self.last_value is not None:
            # Generate value close to previous with daily pattern influence
            base_drift = random.uniform(-20.0, 20.0)
            
            # Add daily pattern influence
            if 6 <= current_hour <= 18:  # Daytime
                pattern_influence = random.uniform(0, 50)
            else:  # Nighttime
                pattern_influence = random.uniform(-30, 0)
            
            new_value = self.last_value + base_drift + pattern_influence
            
            # Keep within reasonable bounds
            new_value = max(self.min_lux + 10, min(self.max_lux - 50, new_value))
        else:
            # First reading based on time of day
            if 6 <= current_hour <= 18:  # Daytime
                new_value = random.uniform(200, 800)
            else:  # Nighttime
                new_value = random.uniform(0, 100)
        
        return round(new_value, 2)
    
    def create_payload(self, luminosity: float) -> Dict[str, Any]:
        """Create MQTT payload with sensor data."""
        anomaly = self.detect_anomaly(luminosity)
        
        payload = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "luminosity",
            "value": luminosity,
            "unit": "lux",
            "sensor_id": self.sensor_id,
            "origin": "edge",
            "anomaly": anomaly
        }
        
        if anomaly:
            payload["anomaly_details"] = {
                "out_of_range": luminosity < self.min_lux or luminosity > self.max_lux,
                "sudden_jump": self.last_value is not None and abs(luminosity - self.last_value) > self.jump_threshold,
                "previous_value": self.last_value
            }
        
        return payload
    
    def publish_reading(self):
        """Generate and publish a single luminosity reading."""
        try:
            luminosity = self.generate_luminosity()
            payload = self.create_payload(luminosity)
            
            # Publish to MQTT
            result = self.client.publish(self.topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "ANOMALY" if payload["anomaly"] else "NORMAL"
                logger.info(f"Published luminosity: {luminosity} lux [{status}]")
            else:
                logger.error(f"Failed to publish message. Return code: {result.rc}")
            
            # Update last value for next anomaly detection
            self.last_value = luminosity
            
        except Exception as e:
            logger.error(f"Error publishing reading: {e}")
    
    def run(self):
        """Main sensor loop."""
        try:
            # Connect to MQTT broker
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()
            
            logger.info(f"Luminosity sensor {self.sensor_id} started")
            logger.info(f"Publishing to topic: {self.topic}")
            
            while True:
                self.publish_reading()
                time.sleep(4)  # Publish every 4 seconds
                
        except KeyboardInterrupt:
            logger.info("Sensor stopped by user")
        except Exception as e:
            logger.error(f"Sensor error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    sensor = LuminositySensor()
    sensor.run()