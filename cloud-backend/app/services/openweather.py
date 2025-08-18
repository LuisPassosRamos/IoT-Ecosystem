import os
import logging
from typing import Optional, Dict, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenWeatherService:
    """Service for interacting with OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = 10.0
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured. Weather features will be disabled.")
    
    async def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Get current weather data for a city."""
        if not self.api_key:
            logger.error("OpenWeatherMap API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"  # Use Celsius
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract relevant information
                weather_data = {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "pressure": data["main"]["pressure"],
                    "feels_like": data["main"]["feels_like"],
                    "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "openweathermap"
                }
                
                logger.info(f"Retrieved weather data for {city}: {weather_data['temperature']}°C, {weather_data['description']}")
                return weather_data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"City not found: {city}")
                return {"error": "City not found", "city": city}
            else:
                logger.error(f"HTTP error getting weather data: {e}")
                return {"error": f"HTTP error: {e.response.status_code}", "city": city}
                
        except httpx.TimeoutException:
            logger.error(f"Timeout getting weather data for {city}")
            return {"error": "Request timeout", "city": city}
            
        except Exception as e:
            logger.error(f"Error getting weather data for {city}: {e}")
            return {"error": str(e), "city": city}
    
    def compare_with_local_sensors(self, weather_data: Dict[str, Any], local_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare weather API data with local sensor readings."""
        comparison = {
            "weather_api": {
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity")
            },
            "local_sensors": {
                "temperature": local_data.get("temperature"),
                "humidity": local_data.get("humidity")
            },
            "differences": {},
            "alerts": []
        }
        
        try:
            # Temperature comparison
            if weather_data.get("temperature") is not None and local_data.get("temperature") is not None:
                temp_diff = abs(weather_data["temperature"] - local_data["temperature"])
                comparison["differences"]["temperature"] = {
                    "absolute_difference": round(temp_diff, 2),
                    "percentage_difference": round((temp_diff / max(weather_data["temperature"], 1)) * 100, 2)
                }
                
                # Check if difference exceeds threshold
                threshold = float(os.getenv("WEATHER_DIFF_THRESHOLD", "5.0"))
                if temp_diff > threshold:
                    comparison["alerts"].append({
                        "type": "temperature_discrepancy",
                        "message": f"Local temperature differs from weather API by {temp_diff:.1f}°C (threshold: {threshold}°C)",
                        "severity": "high" if temp_diff > threshold * 2 else "medium"
                    })
            
            # Humidity comparison
            if weather_data.get("humidity") is not None and local_data.get("humidity") is not None:
                humidity_diff = abs(weather_data["humidity"] - local_data["humidity"])
                comparison["differences"]["humidity"] = {
                    "absolute_difference": round(humidity_diff, 2),
                    "percentage_difference": round((humidity_diff / max(weather_data["humidity"], 1)) * 100, 2)
                }
                
                # Check if humidity difference is significant (>20%)
                if humidity_diff > 20:
                    comparison["alerts"].append({
                        "type": "humidity_discrepancy", 
                        "message": f"Local humidity differs from weather API by {humidity_diff:.1f}% (threshold: 20%)",
                        "severity": "medium"
                    })
            
            comparison["comparison_timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            comparison["has_alerts"] = len(comparison["alerts"]) > 0
            
        except Exception as e:
            logger.error(f"Error comparing weather data: {e}")
            comparison["error"] = str(e)
        
        return comparison
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return self.api_key is not None

# Global OpenWeather service instance
openweather_service = OpenWeatherService()