"""
Scrapers package - prikupljanje podataka sa:
- FBref (statistike, rezultati)
- Understat (xG podaci)
- FIFA (rang liste)
- OpenWeatherMap (vremenski uslovi)
"""

from .fbref_scraper import FBrefScraper
from .understat_scraper import UnderstatScraper
from .fifa_scraper import FIFARankingScraper
from .weather_scraper import WeatherScraper

__all__ = ['FBrefScraper', 'UnderstatScraper', 'FIFARankingScraper', 'WeatherScraper']