 """
Weather Scraper - prikuplja vremenske podatke za utakmice
Podržava:
- Open-Meteo (primarni - ne zahteva API ključ)
- OpenWeatherMap (fallback - zahteva API ključ)
"""

import requests
from datetime import datetime
from typing import Dict, Optional
import json
import os
import random

class WeatherScraper:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicijalizacija weather scraper-a
        
        Args:
            api_key: Opcioni OpenWeatherMap API ključ (nije obavezan)
        """
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', '')
        self.openweather_url = "https://api.openweathermap.org/data/2.5"
        self.openmeteo_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        
    def _get_coordinates_openmeteo(self, city: str) -> Optional[tuple]:
        """Dohvata koordinate grada koristeći Open-Meteo geocoding (besplatno, bez API ključa)"""
        try:
            params = {'name': city, 'count': 1, 'language': 'en', 'format': 'json'}
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    result = data['results'][0]
                    return (result['latitude'], result['longitude'], result.get('country', ''))
            return None
        except Exception as e:
            print(f"⚠️ Geocoding greška za {city}: {e}")
            return None
    
    def get_weather_openmeteo(self, lat: float, lon: float, date: str) -> Dict:
        """Dohvata vremensku prognozu koristeći Open-Meteo (bez API ključa)"""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_mean",
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "timezone": "auto"
            }
            
            response = requests.get(self.openmeteo_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Open-Meteo vraća podatke za 7 dana, tražimo najbliži datumu
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                
                if 'daily' in data and 'time' in data['daily']:
                    for i, forecast_date in enumerate(data['daily']['time']):
                        if forecast_date == date:
                            return {
                                'temperature': data['daily']['temperature_2m_max'][i],
                                'feels_like': data['daily']['temperature_2m_max'][i] - 2,
                                'humidity': 60,  # Open-Meteo nema humidity u daily, koristi default
                                'wind_speed': 10,  # Može se dodati wind_speed_10m_max
                                'rain_probability': data['daily']['precipitation_probability_mean'][i],
                                'conditions': 'rainy' if data['daily']['precipitation_probability_mean'][i] > 50 else 'cloudy',
                                'source': 'open-meteo'
                            }
                
                # Ako nema daily, koristi current
                if 'current' in data:
                    return {
                        'temperature': data['current']['temperature_2m'],
                        'feels_like': data['current']['temperature_2m'] - 2,
                        'humidity': data['current'].get('relative_humidity_2m', 60),
                        'wind_speed': data['current'].get('wind_speed_10m', 10),
                        'rain_probability': 20,
                        'conditions': 'clear',
                        'source': 'open-meteo'
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Open-Meteo greška: {e}")
            return None
    
    def get_weather_openweather(self, city: str, date: str) -> Dict:
        """Dohvata vremensku prognozu koristeći OpenWeatherMap (zahteva API ključ)"""
        if not self.api_key:
            return None
        
        try:
            # Prvo dohvati koordinate grada
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': city,
                'limit': 1,
                'appid': self.api_key
            }
            
            geo_response = requests.get(geo_url, params=params, timeout=10)
            geo_data = geo_response.json()
            
            if not geo_data:
                return None
            
            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
            
            # Dohvati prognozu
            weather_url = f"{self.openweather_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(weather_url, params=params, timeout=10)
            data = response.json()
            
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            for forecast in data.get('list', []):
                forecast_date = datetime.fromtimestamp(forecast['dt']).date()
                if forecast_date == target_date:
                    return {
                        'temperature': forecast['main']['temp'],
                        'feels_like': forecast['main']['feels_like'],
                        'humidity': forecast['main']['humidity'],
                        'wind_speed': forecast['wind']['speed'],
                        'rain_probability': forecast.get('pop', 0) * 100,
                        'conditions': forecast['weather'][0]['description'],
                        'source': 'openweathermap'
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ OpenWeatherMap greška za {city}: {e}")
            return None
    
    def get_weather_for_match(self, city: str, date: str) -> Dict:
        """
        Dohvata vremensku prognozu za grad i datum
        Pokušava redom: Open-Meteo → OpenWeatherMap → Mock
        
        Args:
            city: Ime grada (npr. "Mexico City", "Doha")
            date: Datum u formatu "YYYY-MM-DD"
            
        Returns:
            Dict sa vremenskim podacima
        """
        print(f"🌤️ Dohvatam vreme za {city}, {date}...")
        
        # 1. Pokušaj Open-Meteo (bez API ključa)
        coords = self._get_coordinates_openmeteo(city)
        if coords:
            lat, lon, country = coords
            weather = self.get_weather_openmeteo(lat, lon, date)
            if weather:
                print(f"   ✅ Vreme dohvaćeno preko Open-Meteo")
                return weather
        
        # 2. Pokušaj OpenWeatherMap (ako ima API ključ)
        if self.api_key:
            weather = self.get_weather_openweather(city, date)
            if weather:
                print(f"   ✅ Vreme dohvaćeno preko OpenWeatherMap")
                return weather
        
        # 3. Fallback na mock podatke
        print(f"   ⚠️ Koristim mock podatke za {city}")
        return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict:
        """Generiše mock podatke za demo (kada nema API-ja)"""
        
        # Tipični vremenski uslovi za različite gradove
        weather_patterns = {
            'Mexico City': {'temp': 22, 'conditions': 'sunny', 'rain': 10},
            'Doha': {'temp': 35, 'conditions': 'clear', 'rain': 0},
            'Berlin': {'temp': 18, 'conditions': 'cloudy', 'rain': 30},
            'London': {'temp': 15, 'conditions': 'rainy', 'rain': 60},
            'Rio': {'temp': 28, 'conditions': 'sunny', 'rain': 20},
            'Belgrade': {'temp': 20, 'conditions': 'sunny', 'rain': 15},
            'Paris': {'temp': 17, 'conditions': 'cloudy', 'rain': 25},
            'Madrid': {'temp': 25, 'conditions': 'sunny', 'rain': 10},
            'Munich': {'temp': 16, 'conditions': 'rainy', 'rain': 40},
        }
        
        pattern = weather_patterns.get(city, {'temp': 20, 'conditions': 'clear', 'rain': 15})
        
        return {
            'temperature': pattern['temp'] + random.uniform(-5, 5),
            'feels_like': pattern['temp'] + random.uniform(-3, 3),
            'humidity': random.randint(40, 80),
            'wind_speed': random.uniform(0, 15),
            'rain_probability': pattern['rain'] + random.uniform(-10, 20),
            'conditions': pattern['conditions'],
            'icon': '01d' if pattern['conditions'] == 'sunny' else '03d',
            'source': 'mock'
        }
    
    def get_weather_factors(self, weather_data: Dict) -> Dict:
        """
        Konvertuje vremenske podatke u faktore za ML model
        
        Returns:
            Dict sa faktorima (0-1 skala):
            - heat_factor: uticaj vrućine (veća temp = veći umor)
            - rain_factor: uticaj kiše (lošije za tehničke timove)
            - wind_factor: uticaj vetra
            - fatigue_factor: ukupni faktor zamora od vremena
        """
        temp = weather_data.get('temperature', 20)
        rain = weather_data.get('rain_probability', 20)
        wind = weather_data.get('wind_speed', 5)
        
        # Faktori od 0 do 1
        heat_factor = max(0, min(1, (temp - 25) / 15)) if temp > 25 else 0
        rain_factor = rain / 100
        wind_factor = max(0, min(1, wind / 20))
        
        # Kombinovani faktor zamora
        fatigue_factor = (heat_factor + rain_factor + wind_factor) / 3
        
        return {
            'heat_factor': round(heat_factor, 2),
            'rain_factor': round(rain_factor, 2),
            'wind_factor': round(wind_factor, 2),
            'fatigue_factor': round(fatigue_factor, 2),
            'advantage_attacking': round(1 - rain_factor, 2),
            'advantage_defending': round(1 - wind_factor, 2),
            'source': weather_data.get('source', 'unknown')
        }


# Testiranje
if __name__ == "__main__":
    print("="*50)
    print("🌤️ TESTIRANJE WEATHER SCRAPER-a")
    print("="*50)
    
    scraper = WeatherScraper()  # Bez API ključa - koristi Open-Meteo
    
    # Test za Mexico City
    weather = scraper.get_weather_for_match("Mexico City", "2026-06-11")
    print(f"\n📊 Vreme u Mexico City-ju:")
    print(f"   Temperatura: {weather.get('temperature', '?')}°C")
    print(f"   Kiša: {weather.get('rain_probability', '?')}%")
    print(f"   Izvor: {weather.get('source', '?')}")
    
    factors = scraper.get_weather_factors(weather)
    print(f"\n📈 Faktori za ML model:")
    for key, value in factors.items():
        print(f"   {key}: {value}")