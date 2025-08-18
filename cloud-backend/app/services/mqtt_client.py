import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

logger = logging.getLogger(__name__)

class MQTTClientService:
    """MQTT client service for subscribing to sensor data."""
    
    def __init__(self):
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_handler: Optional[Callable[[str, Dict[str, Any]], None]] = None
        
        # Topic subscriptions
        self.topics = [
            "sensors/temperature/+",
            "sensors/humidity/+", 
            "sensors/luminosity/+"
        ]
    
    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Set the message handler function."""
        self.message_handler = handler
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client connects to the broker."""
        if reason_code.is_failure:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
            self.connected = False
        else:
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            self.connected = True
            
            # Subscribe to all sensor topics
            for topic in self.topics:
                result = client.subscribe(topic, qos=1)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Subscribed to topic: {topic}")
                else:
                    logger.error(f"Failed to subscribe to topic {topic}: {result}")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        if reason_code.is_failure:
            logger.warning(f"Unexpected disconnection from MQTT broker: {reason_code}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_message(self, client, userdata, message):
        """Callback for when a message is received."""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode('utf-8'))
            
            logger.info(f"Received MQTT message on topic {topic}: {payload.get('type', 'unknown')} = {payload.get('value', 'N/A')}")
            
            # Call the message handler if set
            if self.message_handler:
                asyncio.create_task(self._async_message_handler(topic, payload))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode MQTT message payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def _async_message_handler(self, topic: str, payload: Dict[str, Any]):
        """Async wrapper for message handler."""
        try:
            if self.message_handler:
                await self.message_handler(topic, payload)
        except Exception as e:
            logger.error(f"Error in async message handler: {e}")
    
    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        """Callback for when a subscription is confirmed."""
        for reason_code in reason_code_list:
            if reason_code.is_failure:
                logger.error(f"Subscription failed: {reason_code}")
            else:
                logger.debug(f"Subscription confirmed with QoS: {reason_code.value}")
    
    def on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logging."""
        if level <= mqtt.MQTT_LOG_WARNING:
            logger.warning(f"MQTT: {buf}")
        elif level <= mqtt.MQTT_LOG_INFO:
            logger.info(f"MQTT: {buf}")
        else:
            logger.debug(f"MQTT: {buf}")
    
    async def connect(self):
        """Connect to the MQTT broker."""
        try:
            # Create MQTT client with callback API version 2
            self.client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id="iot-backend-service"
            )
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_log = self.on_log
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}")
            await asyncio.to_thread(self.client.connect, self.host, self.port, 60)
            
            # Start the network loop in a separate thread
            self.client.loop_start()
            
            # Wait a bit for connection to establish
            await asyncio.sleep(1)
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.connected
    
    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """Publish a message to a topic."""
        if not self.client or not self.connected:
            logger.error("Cannot publish: MQTT client not connected")
            return False
        
        try:
            message_json = json.dumps(payload)
            result = self.client.publish(topic, message_json, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to topic {topic}")
                return True
            else:
                logger.error(f"Failed to publish message to topic {topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

# Global MQTT client instance
mqtt_client = MQTTClientService()