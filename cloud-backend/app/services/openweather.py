"""
OpenWeatherMap API integration service
"""

import os
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.schemas import WeatherResponse

logger = logging.getLogger(__name__)

class OpenWeatherService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.default_city = os.getenv("DEFAULT_CITY", "London")
        
        if not self.api_key:
            logger.warning("OpenWeather API key not configured - weather features will return mock data")
    
    async def get_weather(self, city: str = None) -> Optional[WeatherResponse]:
        """Get current weather data for a city"""
        city = city or self.default_city
        
        if not self.api_key:
            # Return mock data when API key is not configured
            return self._get_mock_weather(city)
        
        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"  # Celsius
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                weather_data = WeatherResponse(
                    city=data["name"],
                    temperature=float(data["main"]["temp"]),
                    humidity=float(data["main"]["humidity"]),
                    pressure=float(data["main"]["pressure"]),
                    description=data["weather"][0]["description"],
                    timestamp=datetime.utcnow()
                )
                
                logger.info(f"Retrieved weather data for {city}: {weather_data.temperature}°C")
                return weather_data
                
            elif response.status_code == 401:
                logger.error("Invalid OpenWeather API key")
                return self._get_mock_weather(city)
            elif response.status_code == 404:
                logger.error(f"City not found: {city}")
                return None
            else:
                logger.error(f"OpenWeather API error: {response.status_code}")
                return self._get_mock_weather(city)
                
        except requests.exceptions.Timeout:
            logger.error("OpenWeather API request timeout")
            return self._get_mock_weather(city)
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API request failed: {e}")
            return self._get_mock_weather(city)
        except Exception as e:
            logger.error(f"Unexpected error getting weather data: {e}")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> WeatherResponse:
        """Return mock weather data when API is not available"""
        import random
        
        # Generate realistic weather data based on city
        base_temp = 20.0
        if city.lower() in ["london", "manchester", "glasgow"]:
            base_temp = 15.0
        elif city.lower() in ["madrid", "barcelona", "sevilla"]:
            base_temp = 25.0
        elif city.lower() in ["stockholm", "oslo", "helsinki"]:
            base_temp = 10.0
        
        mock_data = WeatherResponse(
            city=city,
            temperature=round(base_temp + random.uniform(-5, 5), 1),
            humidity=round(random.uniform(40, 80), 1),
            pressure=round(random.uniform(1000, 1025), 1),
            description=random.choice([
                "clear sky", "few clouds", "scattered clouds", 
                "broken clouds", "light rain", "moderate rain"
            ]),
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Using mock weather data for {city}: {mock_data.temperature}°C")
        return mock_data
    
    def compare_with_sensor(self, weather_data: WeatherResponse, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare weather data with local sensor data"""
        comparison = {
            "weather": {
                "temperature": weather_data.temperature,
                "humidity": weather_data.humidity,
                "pressure": weather_data.pressure
            },
            "sensor": {},
            "differences": {},
            "alerts": []
        }
        
        # Temperature comparison
        if "temperature" in sensor_data:
            sensor_temp = sensor_data["temperature"]
            comparison["sensor"]["temperature"] = sensor_temp
            temp_diff = abs(weather_data.temperature - sensor_temp)
            comparison["differences"]["temperature"] = temp_diff
            
            # Alert if difference is significant (>5°C)
            if temp_diff > 5.0:
                comparison["alerts"].append({
                    "type": "temperature_discrepancy",
                    "message": f"Large temperature difference: sensor {sensor_temp}°C vs weather {weather_data.temperature}°C",
                    "severity": "warning" if temp_diff <= 10 else "critical"
                })
        
        # Humidity comparison
        if "humidity" in sensor_data:
            sensor_humidity = sensor_data["humidity"]
            comparison["sensor"]["humidity"] = sensor_humidity
            humidity_diff = abs(weather_data.humidity - sensor_humidity)
            comparison["differences"]["humidity"] = humidity_diff
            
            # Alert if difference is significant (>20%)
            if humidity_diff > 20.0:
                comparison["alerts"].append({
                    "type": "humidity_discrepancy",
                    "message": f"Large humidity difference: sensor {sensor_humidity}% vs weather {weather_data.humidity}%",
                    "severity": "warning" if humidity_diff <= 30 else "critical"
                })
        
        # Pressure comparison (if available from sensors)
        if "pressure" in sensor_data:
            sensor_pressure = sensor_data["pressure"]
            comparison["sensor"]["pressure"] = sensor_pressure
            pressure_diff = abs(weather_data.pressure - sensor_pressure)
            comparison["differences"]["pressure"] = pressure_diff
            
            # Alert if difference is significant (>10 hPa)
            if pressure_diff > 10.0:
                comparison["alerts"].append({
                    "type": "pressure_discrepancy",
                    "message": f"Large pressure difference: sensor {sensor_pressure} hPa vs weather {weather_data.pressure} hPa",
                    "severity": "warning"
                })
        
        return comparison

# Global service instance
openweather_service: Optional[OpenWeatherService] = None

def get_openweather_service() -> OpenWeatherService:
    """Get the global OpenWeather service instance"""
    global openweather_service
    if openweather_service is None:
        openweather_service = OpenWeatherService()
    return openweather_service