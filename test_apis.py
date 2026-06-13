
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_sportmonks():
    print("\n⚽ Testiram Sportmonks (token u URL-u)...")
    token = os.getenv('SPORTMONKS_TOKEN')
    
    if not token:
        print("   ❌ Nema API ključa u .env fajlu!")
        return False

    # ISPRAVAN URL: token ide kao parametar, NE kao header
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay?api_token={token}&include=participants;scores"
    
    try:
        response = requests.get(url, timeout=15)  # Bez headers!
        
        if response.status_code == 200:
            print("   ✅ Sportmonks radi!")
            return True
        elif response.status_code == 401:
            print("   ❌ Greška 401: API token nije ispravan. Proveri token na dashboard-u.")
            return False
        else:
            print(f"   ❌ Greška: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Greška pri povezivanju: {e}")
        return False
   
    
def test_football_api():
    print("\n⚽ Testiram Football-Data.org...")
    token = os.getenv('FOOTBALL_DATA_API_KEY')
    
    if not token:
        print("   ❌ Nema API ključa u .env fajlu!")
        return False
    
    headers = {'X-Auth-Token': token}
    url = "https://api.football-data.org/v4/competitions/"
    
    try:
        # verify=False zaobilazi SSL problem
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Football-Data.org radi! ({len(data.get('competitions', []))} takmičenja)")
            return True
        else:
            print(f"   ❌ Greška: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Greška: {e}")
        return False
                
def test_weather():
    print("\n🌤️ Testiram Weather scraper...")
    try:
        from backend.scrapers.weather_scraper import WeatherScraper
        
        scraper = WeatherScraper()
        weather = scraper.get_weather_for_match("Belgrade", "2026-06-13")
        
        if weather:
            print(f"   ✅ Weather radi! (Izvor: {weather.get('source', 'unknown')})")
            print(f"   Temperatura: {weather.get('temperature', '?')}°C")
            return True
        else:
            print(f"   ❌ Weather ne vraća podatke")
            return False
    except Exception as e:
        print(f"   ❌ Greška: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🔑 TESTIRANJE API KLJUČEVA")
    print("="*50)
    
    football_ok = test_football_api()
    sportmonks_ok = test_sportmonks()
    weather_ok = test_weather()
    
    print("\n" + "="*50)
    print("📊 REZIME:")
    print(f"   Football-Data.org: {'✅ RADI' if football_ok else '❌ NE RADI'}")
    print(f"   Sportmonks: {'✅ RADI' if sportmonks_ok else '❌ NE RADI'}")
    print(f"   Weather: {'✅ RADI' if weather_ok else '❌ NE RADI'}")
    print("="*50)