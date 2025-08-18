#!/usr/bin/env python3
"""
CoAP sensor simulator.
Simulates a CoAP server that provides sensor readings for the Fog layer to bridge to MQTT.
"""

import asyncio
import json
import logging
import random
import os
from datetime import datetime
from typing import Dict, Any

import aiocoap.resource as resource
import aiocoap

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TemperatureCoapResource(resource.Resource):
    """CoAP resource for temperature readings."""
    
    def __init__(self):
        super().__init__()
        self.sensor_id = "coap_temp_001"
        self.last_reading = None
        self.reading_count = 0
    
    async def render_get(self, request):
        """Handle GET requests for temperature data."""
        try:
            # Generate temperature reading
            temperature = round(random.uniform(20.0, 28.0), 2)
            
            payload = {
                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": "temperature",
                "value": temperature,
                "unit": "celsius",
                "sensor_id": self.sensor_id,
                "origin": "coap",
                "protocol": "coap",
                "reading_count": self.reading_count
            }
            
            self.last_reading = payload
            self.reading_count += 1
            
            logger.info(f"CoAP GET: Temperature {temperature}°C [reading #{self.reading_count}]")
            
            return aiocoap.Message(
                content_format=aiocoap.numbers.media_types_rev['application/json'],
                payload=json.dumps(payload).encode('utf-8')
            )
            
        except Exception as e:
            logger.error(f"Error in CoAP temperature resource: {e}")
            return aiocoap.Message(code=aiocoap.numbers.codes.Code.INTERNAL_SERVER_ERROR)

class HumidityCoapResource(resource.Resource):
    """CoAP resource for humidity readings."""
    
    def __init__(self):
        super().__init__()
        self.sensor_id = "coap_humidity_001"
        self.last_reading = None
        self.reading_count = 0
    
    async def render_get(self, request):
        """Handle GET requests for humidity data."""
        try:
            # Generate humidity reading
            humidity = round(random.uniform(45.0, 75.0), 2)
            
            payload = {
                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": "humidity",
                "value": humidity,
                "unit": "percent",
                "sensor_id": self.sensor_id,
                "origin": "coap",
                "protocol": "coap",
                "reading_count": self.reading_count
            }
            
            self.last_reading = payload
            self.reading_count += 1
            
            logger.info(f"CoAP GET: Humidity {humidity}% [reading #{self.reading_count}]")
            
            return aiocoap.Message(
                content_format=aiocoap.numbers.media_types_rev['application/json'],
                payload=json.dumps(payload).encode('utf-8')
            )
            
        except Exception as e:
            logger.error(f"Error in CoAP humidity resource: {e}")
            return aiocoap.Message(code=aiocoap.numbers.codes.Code.INTERNAL_SERVER_ERROR)

class StatusCoapResource(resource.Resource):
    """CoAP resource for server status."""
    
    def __init__(self, temp_resource, humidity_resource):
        super().__init__()
        self.temp_resource = temp_resource
        self.humidity_resource = humidity_resource
        self.start_time = datetime.utcnow()
    
    async def render_get(self, request):
        """Handle GET requests for server status."""
        try:
            uptime = datetime.utcnow() - self.start_time
            
            status = {
                "status": "online",
                "uptime_seconds": int(uptime.total_seconds()),
                "server_type": "coap_sensor_simulator",
                "resources": {
                    "temperature": {
                        "path": "/temperature",
                        "readings_served": self.temp_resource.reading_count,
                        "last_reading": self.temp_resource.last_reading
                    },
                    "humidity": {
                        "path": "/humidity", 
                        "readings_served": self.humidity_resource.reading_count,
                        "last_reading": self.humidity_resource.last_reading
                    }
                },
                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            logger.info(f"CoAP Status requested - Uptime: {uptime}")
            
            return aiocoap.Message(
                content_format=aiocoap.numbers.media_types_rev['application/json'],
                payload=json.dumps(status, indent=2).encode('utf-8')
            )
            
        except Exception as e:
            logger.error(f"Error in CoAP status resource: {e}")
            return aiocoap.Message(code=aiocoap.numbers.codes.Code.INTERNAL_SERVER_ERROR)

async def main():
    """Main CoAP server function."""
    try:
        # Create resources
        temp_resource = TemperatureCoapResource()
        humidity_resource = HumidityCoapResource()
        status_resource = StatusCoapResource(temp_resource, humidity_resource)
        
        # Setup resource tree
        root = resource.Site()
        root.add_resource(['temperature'], temp_resource)
        root.add_resource(['humidity'], humidity_resource)
        root.add_resource(['status'], status_resource)
        
        # Get configuration
        coap_host = os.getenv("COAP_HOST", "localhost")
        coap_port = int(os.getenv("COAP_PORT", "5683"))
        
        # Start CoAP server
        await aiocoap.Context.create_server_context(root, bind=(coap_host, coap_port))
        
        logger.info(f"CoAP sensor simulator started on {coap_host}:{coap_port}")
        logger.info("Available resources:")
        logger.info(f"  - coap://{coap_host}:{coap_port}/temperature")
        logger.info(f"  - coap://{coap_host}:{coap_port}/humidity")
        logger.info(f"  - coap://{coap_host}:{coap_port}/status")
        
        # Keep server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("CoAP server stopped by user")
    except Exception as e:
        logger.error(f"CoAP server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())