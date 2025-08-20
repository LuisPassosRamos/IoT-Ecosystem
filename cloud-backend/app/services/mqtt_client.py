"""
MQTT client service for subscribing to sensor data and publishing to WebSocket
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Callable, Optional
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.models.schemas import SensorReading, get_db, SessionLocal

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self, host: str, port: int = 1883):
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id="iot-backend")
        self.connected = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.websocket_callbacks: Set[Callable] = set()
        self.latest_readings: Dict[str, Dict] = {}
        
        # Setup MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when MQTT client connects"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            
            # Subscribe to all sensor topics
            topics = [
                ("sensors/+/+", 1),  # All sensor data
                ("nodered/status", 0),  # Node-RED status
                ("system/+", 0)  # System messages
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when MQTT client disconnects"""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received MQTT message - Topic: {topic}, Payload: {payload}")
            
            # Handle sensor data
            if topic.startswith("sensors/"):
                self._handle_sensor_data(topic, payload)
            elif topic.startswith("nodered/"):
                self._handle_nodered_status(topic, payload)
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _handle_sensor_data(self, topic: str, payload: str):
        """Process sensor data and store in database"""
        try:
            # Parse topic: sensors/{type}/{sensor_id}
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                sensor_type = topic_parts[1]
                sensor_id = topic_parts[2]
            else:
                logger.warning(f"Invalid topic format: {topic}")
                return
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in sensor data: {payload}")
                return
            
            # Validate required fields
            if 'value' not in data:
                logger.warning(f"Missing 'value' field in sensor data: {data}")
                return
            
            # Extract data with defaults
            timestamp_str = data.get('ts', data.get('timestamp'))
            if timestamp_str:
                try:
                    if timestamp_str.endswith('Z'):
                        timestamp = datetime.fromisoformat(timestamp_str[:-1])
                    else:
                        timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Create sensor reading
            reading_data = {
                'timestamp': timestamp,
                'sensor_type': data.get('type', sensor_type),
                'sensor_id': data.get('sensor_id', sensor_id),
                'value': float(data['value']),
                'unit': data.get('unit', ''),
                'origin': data.get('origin', 'unknown'),
                'source_protocol': data.get('source_protocol', 'mqtt'),
                'anomaly': data.get('anomaly', False),
                'raw_data': payload
            }
            
            # Store in database
            self._store_sensor_reading(reading_data)
            
            # Update latest readings cache
            self.latest_readings[f"{sensor_type}_{sensor_id}"] = reading_data
            
            # Prepare WebSocket-safe payload (datetime -> ISO string)
            ws_data = reading_data.copy()
            ts = ws_data.get('timestamp')
            if isinstance(ts, datetime):
                ws_data['timestamp'] = ts.isoformat()

            # Notify WebSocket clients
            self._notify_websocket_clients({
                'type': 'sensor_data',
                'data': ws_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    def _handle_nodered_status(self, topic: str, payload: str):
        """Handle Node-RED status messages"""
        logger.info(f"Node-RED status - {topic}: {payload}")
        
        # Notify WebSocket clients about Node-RED status
        self._notify_websocket_clients({
            'type': 'system_status',
            'data': {
                'service': 'node-red',
                'status': payload,
                'topic': topic
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def _store_sensor_reading(self, reading_data: dict):
        """Store sensor reading in database"""
        try:
            db = SessionLocal()
            try:
                reading = SensorReading(**reading_data)
                db.add(reading)
                db.commit()
                logger.debug(f"Stored sensor reading: {reading_data['sensor_id']}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error storing sensor reading: {e}")
    
    def _notify_websocket_clients(self, message: dict):
        """Notify all connected WebSocket clients from MQTT thread safely."""
        if not self.websocket_callbacks:
            return
        if not self.loop or not self.loop.is_running():
            logger.error("No running event loop set on MQTTService")
            return
        for callback in self.websocket_callbacks:
            try:
                fut = asyncio.run_coroutine_threadsafe(callback(message), self.loop)
                # Log exceptions raised inside the callback
                def _done(f):
                    try:
                        f.result()
                    except Exception as exc:
                        logger.error(f"WebSocket callback error: {exc}")
                fut.add_done_callback(_done)
            except Exception as e:
                logger.error(f"Error notifying WebSocket client: {e}")
    
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set asyncio loop to schedule async callbacks from MQTT thread."""
        self.loop = loop

    def add_websocket_callback(self, cb: Callable):
        """Add WebSocket callback for real-time updates"""
        self.websocket_callbacks.add(cb)
    
    def remove_websocket_callback(self, callback: Callable):
        """Remove WebSocket callback"""
        self.websocket_callbacks.discard(callback)
    
    def get_latest_readings(self) -> Dict[str, Dict]:
        """Get latest sensor readings from cache"""
        return self.latest_readings.copy()
    
    def start(self):
        """Start MQTT client"""
        try:
            logger.info(f"Starting MQTT client - connecting to {self.host}:{self.port}")
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            return False
    
    def stop(self):
        """Stop MQTT client"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")
    
    def publish(self, topic: str, payload: str, qos: int = 1):
        """Publish message to MQTT topic"""
        if self.connected:
            try:
                result = self.client.publish(topic, payload, qos)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"Published to {topic}: {payload}")
                    return True
                else:
                    logger.error(f"Failed to publish to {topic}: {result.rc}")
                    return False
            except Exception as e:
                logger.error(f"Error publishing to MQTT: {e}")
                return False
        else:
            logger.warning("Cannot publish - MQTT client not connected")
            return False

# Global MQTT service instance
mqtt_service: Optional[MQTTService] = None

def get_mqtt_service() -> MQTTService:
    """Get the global MQTT service instance"""
    global mqtt_service
    if mqtt_service is None:
        raise RuntimeError("MQTT service not initialized")
    return mqtt_service

def init_mqtt_service(host: str, port: int = 1883) -> MQTTService:
    """Initialize the global MQTT service"""
    global mqtt_service
    mqtt_service = MQTTService(host, port)
    return mqtt_service