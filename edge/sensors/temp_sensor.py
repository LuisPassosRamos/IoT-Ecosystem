#!/usr/bin/env python3
"""
Temperature sensor simulator with anomaly detection.
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

class TemperatureSensor:
    def __init__(self):
        # MQTT Configuration
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic = "sensors/temperature/sim001"
        
        # Sensor configuration
        self.sensor_id = "temp_sim_001"
        self.min_temp = float(os.getenv("TEMP_MIN", "15.0"))
        self.max_temp = float(os.getenv("TEMP_MAX", "35.0"))
        self.jump_threshold = float(os.getenv("TEMP_JUMP_THRESHOLD", "5.0"))
        
        # State tracking for anomaly detection
        self.last_value: Optional[float] = None
        self.anomaly_probability = 0.05  # 5% chance of anomaly
        
        # MQTT Client
        self.client = mqtt.Client(client_id=f"temp-sensor-{self.sensor_id}")
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
        if value < self.min_temp or value > self.max_temp:
            anomaly = True
            logger.warning(f"Range anomaly detected: {value}°C (valid range: {self.min_temp}-{self.max_temp}°C)")
        
        # Jump-based anomaly
        if self.last_value is not None:
            jump = abs(value - self.last_value)
            if jump > self.jump_threshold:
                anomaly = True
                logger.warning(f"Jump anomaly detected: {jump}°C change from {self.last_value}°C to {value}°C")
        
        return anomaly
    
    def generate_temperature(self) -> float:
        """Generate temperature reading with occasional anomalies."""
        if random.random() < self.anomaly_probability:
            # Generate anomalous reading
            if random.choice([True, False]):
                # Out of range anomaly
                return round(random.choice([
                    random.uniform(self.min_temp - 10, self.min_temp - 1),  # Too cold
                    random.uniform(self.max_temp + 1, self.max_temp + 10)   # Too hot
                ]), 2)
            else:
                # Jump anomaly (if we have previous value)
                if self.last_value is not None:
                    jump_direction = random.choice([-1, 1])
                    jump_size = random.uniform(self.jump_threshold + 1, self.jump_threshold + 5)
                    return round(self.last_value + (jump_direction * jump_size), 2)
        
        # Normal reading
        if self.last_value is not None:
            # Generate value close to previous (normal drift)
            drift = random.uniform(-2.0, 2.0)
            new_value = self.last_value + drift
            # Keep within reasonable bounds
            new_value = max(self.min_temp + 2, min(self.max_temp - 2, new_value))
        else:
            # First reading
            new_value = random.uniform(self.min_temp + 2, self.max_temp - 2)
        
        return round(new_value, 2)
    
    def create_payload(self, temperature: float) -> Dict[str, Any]:
        """Create MQTT payload with sensor data."""
        anomaly = self.detect_anomaly(temperature)
        
        payload = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "temperature",
            "value": temperature,
            "unit": "celsius",
            "sensor_id": self.sensor_id,
            "origin": "edge",
            "anomaly": anomaly
        }
        
        if anomaly:
            payload["anomaly_details"] = {
                "out_of_range": temperature < self.min_temp or temperature > self.max_temp,
                "sudden_jump": self.last_value is not None and abs(temperature - self.last_value) > self.jump_threshold,
                "previous_value": self.last_value
            }
        
        return payload
    
    def publish_reading(self):
        """Generate and publish a single temperature reading."""
        try:
            temperature = self.generate_temperature()
            payload = self.create_payload(temperature)
            
            # Publish to MQTT
            result = self.client.publish(self.topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "ANOMALY" if payload["anomaly"] else "NORMAL"
                logger.info(f"Published temperature: {temperature}°C [{status}]")
            else:
                logger.error(f"Failed to publish message. Return code: {result.rc}")
            
            # Update last value for next anomaly detection
            self.last_value = temperature
            
        except Exception as e:
            logger.error(f"Error publishing reading: {e}")
    
    def run(self):
        """Main sensor loop."""
        try:
            # Connect to MQTT broker
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()
            
            logger.info(f"Temperature sensor {self.sensor_id} started")
            logger.info(f"Publishing to topic: {self.topic}")
            
            while True:
                self.publish_reading()
                time.sleep(2)  # Publish every 2 seconds
                
        except KeyboardInterrupt:
            logger.info("Sensor stopped by user")
        except Exception as e:
            logger.error(f"Sensor error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    sensor = TemperatureSensor()
    sensor.run()