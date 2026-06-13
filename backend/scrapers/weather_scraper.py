"""
Weather Scraper - prikuplja vremenske podatke za utakmice
"""

import requests
from datetime import datetime
from typing import Dict, Optional
import random
import os

class WeatherScraper:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', '')
        self.openmeteo_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather_for_match(self, city: str, date: str) -> Dict:
        """Dohvata vremensku prognozu za grad"""
        try:
            # Open-Meteo geocoding
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {'name': city, 'count': 1, 'format': 'json'}
            geo_response = requests.get(geo_url, params=params, timeout=10)
            
            if geo_response.status_code == 200:
                data = geo_response.json()
                if data.get('results'):
                    lat = data['results'][0]['latitude']
                    lon = data['results'][0]['longitude']
                    
                    # Dohvati vremensku prognozu
                    weather_params = {
                        'latitude': lat,
                        'longitude': lon,
                        'daily': 'temperature_2m_max,precipitation_probability_mean',
                        'timezone': 'auto'
                    }
                    weather_response = requests.get(self.openmeteo_url, params=weather_params, timeout=10)
                    
                    if weather_response.status_code == 200:
                        weather_data = weather_response.json()
                        if 'daily' in weather_data:
                            return {
                                'temperature': weather_data['daily']['temperature_2m_max'][0],
                                'rain_probability': weather_data['daily']['precipitation_probability_mean'][0],
                                'conditions': 'rainy' if weather_data['daily']['precipitation_probability_mean'][0] > 50 else 'clear',
                                'source': 'open-meteo'
                            }
        except Exception as e:
            print(f"⚠️ Weather greška: {e}")
        
        return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict:
        """Mock podaci"""
        weather_patterns = {
            'Mexico City': {'temp': 22, 'rain': 10},
            'Belgrade': {'temp': 20, 'rain': 15},
            'London': {'temp': 15, 'rain': 60},
        }
        pattern = weather_patterns.get(city, {'temp': 20, 'rain': 15})
        
        return {
            'temperature': pattern['temp'] + random.uniform(-3, 3),
            'rain_probability': pattern['rain'] + random.uniform(-10, 20),
            'conditions': 'cloudy',
            'source': 'mock'
        }
    
    def get_weather_factors(self, weather_data: Dict) -> Dict:
        """Konvertuje vreme u ML faktore"""
        rain = weather_data.get('rain_probability', 20)
        return {
            'rain_factor': round(rain / 100, 2),
            'advantage_attacking': round(1 - (rain / 100), 2),
            'source': weather_data.get('source', 'unknown')
        }


if __name__ == "__main__":
    scraper = WeatherScraper()
    weather = scraper.get_weather_for_match("Belgrade", "2026-06-13")
    print(weather)