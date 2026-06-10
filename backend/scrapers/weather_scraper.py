"""
Weather Scraper - prikuplja vremenske podatke za utakmice
Koristi OpenWeatherMap API (besplatni API ključ potreban)
"""

import requests
from datetime import datetime
from typing import Dict, Optional
import json
import os

class WeatherScraper:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicijalizacija weather scraper-a
        
        Args:
            api_key: OpenWeatherMap API ključ (može se dobiti besplatno na openweathermap.org)
        """
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_weather_for_match(self, city: str, date: str) -> Dict:
        """
        Dohvata vremensku prognozu za grad i datum
        
        Args:
            city: Ime grada (npr. "Mexico City", "Doha")
            date: Datum u formatu "YYYY-MM-DD"
            
        Returns:
            Dict sa vremenskim podacima
        """
        if not self.api_key:
            return self._get_mock_weather(city)
        
        try:
            # Prvo dohvati koordinate grada
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': city,
                'limit': 1,
                'appid': self.api_key
            }
            
            geo_response = requests.get(geo_url, params=params)
            geo_data = geo_response.json()
            
            if not geo_data:
                return self._get_mock_weather(city)
            
            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
            
            # Dohvati prognozu za koordinate
            weather_url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(weather_url, params=params)
            data = response.json()
            
            # Pronađi prognozu za traženi datum
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
                        'icon': forecast['weather'][0]['icon']
                    }
            
            return self._get_mock_weather(city)
            
        except Exception as e:
            print(f"Greška pri dohvatanju vremena za {city}: {e}")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict:
        """Generiše mock podatke za demo (kada nema API ključa)"""
        import random
        
        # Tipični vremenski uslovi za različite gradove
        weather_patterns = {
            'Mexico City': {'temp': 22, 'conditions': 'sunny', 'rain': 10},
            'Doha': {'temp': 35, 'conditions': 'clear', 'rain': 0},
            'Berlin': {'temp': 18, 'conditions': 'cloudy', 'rain': 30},
            'London': {'temp': 15, 'conditions': 'rainy', 'rain': 60},
            'Rio': {'temp': 28, 'conditions': 'sunny', 'rain': 20},
        }
        
        pattern = weather_patterns.get(city, {'temp': 20, 'conditions': 'clear', 'rain': 15})
        
        # Dodaj malo random varijacija
        return {
            'temperature': pattern['temp'] + random.uniform(-5, 5),
            'feels_like': pattern['temp'] + random.uniform(-3, 3),
            'humidity': random.randint(40, 80),
            'wind_speed': random.uniform(0, 15),
            'rain_probability': pattern['rain'] + random.uniform(-10, 20),
            'conditions': pattern['conditions'],
            'icon': '01d' if pattern['conditions'] == 'sunny' else '03d',
            'source': 'mock'  # Oznaka da su mock podaci
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
            'advantage_attacking': round(1 - rain_factor, 2),  # Suvo = bolje za napad
            'advantage_defending': round(1 - wind_factor, 2)   # Manje vetra = bolje za odbranu
        }

# Primer korišćenja
if __name__ == "__main__":
    scraper = WeatherScraper()  # Bez API ključa - koristi mock
    
    # Test za Mexico City 11. juna 2026.
    weather = scraper.get_weather_for_match("Mexico City", "2026-06-11")
    print(f"Vreme u Mexico City-ju: {weather}")
    
    factors = scraper.get_weather_factors(weather)
    print(f"\nFaktori za ML model: {factors}")