import requests
from bs4 import BeautifulSoup
import time
import json
from typing import Dict, List, Optional
from datetime import datetime, date
from loguru import logger
from src.config import settings


class RZDScraper:
    def __init__(self):
        self.base_url = settings.rzd_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_tickets(self, departure_station: str, arrival_station: str, 
                      departure_date: date, train_number: Optional[str] = None) -> List[Dict]:
        """
        Поиск билетов на сайте РЖД
        """
        try:
            # Формируем URL для поиска
            search_url = f"{self.base_url}/tickets/public/ru"
            
            # Параметры поиска
            params = {
                'layerName': 'search',
                'ticketSearch[departureStation]': departure_station,
                'ticketSearch[arrivalStation]': arrival_station,
                'ticketSearch[departureDate]': departure_date.strftime('%d.%m.%Y'),
                'ticketSearch[timeFrom]': '00:00',
                'ticketSearch[timeTo]': '23:59'
            }
            
            if train_number:
                params['ticketSearch[trainNumber]'] = train_number
            
            logger.info(f"Поиск билетов: {departure_station} -> {arrival_station} на {departure_date}")
            
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Парсим результаты
            soup = BeautifulSoup(response.content, 'html.parser')
            trains = self._parse_search_results(soup)
            
            logger.info(f"Найдено поездов: {len(trains)}")
            return trains
            
        except Exception as e:
            logger.error(f"Ошибка при поиске билетов: {e}")
            return []
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Парсинг результатов поиска
        """
        trains = []
        
        # Ищем блоки с поездами (это примерная структура, нужно адаптировать под реальный сайт)
        train_blocks = soup.find_all('div', class_='train-item') or soup.find_all('tr', class_='train-row')
        
        for block in train_blocks:
            try:
                train_data = self._parse_train_block(block)
                if train_data:
                    trains.append(train_data)
            except Exception as e:
                logger.warning(f"Ошибка парсинга блока поезда: {e}")
                continue
        
        return trains
    
    def _parse_train_block(self, block) -> Optional[Dict]:
        """
        Парсинг блока с информацией о поезде
        """
        try:
            # Извлекаем номер поезда
            train_number_elem = block.find('span', class_='train-number') or block.find('td', class_='train-number')
            train_number = train_number_elem.text.strip() if train_number_elem else None
            
            # Извлекаем время отправления
            departure_time_elem = block.find('span', class_='departure-time') or block.find('td', class_='departure-time')
            departure_time = departure_time_elem.text.strip() if departure_time_elem else None
            
            # Извлекаем время прибытия
            arrival_time_elem = block.find('span', class_='arrival-time') or block.find('td', class_='arrival-time')
            arrival_time = arrival_time_elem.text.strip() if arrival_time_elem else None
            
            # Извлекаем доступные места
            seats_data = self._parse_available_seats(block)
            
            return {
                'train_number': train_number,
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'available_seats': seats_data,
                'prices': self._extract_prices(block)
            }
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга блока поезда: {e}")
            return None
    
    def _parse_available_seats(self, block) -> Dict:
        """
        Парсинг доступных мест
        """
        seats = {}
        
        # Ищем блоки с типами мест
        seat_types = ['плацкарт', 'купе', 'св', 'сидячие', 'люкс']
        
        for seat_type in seat_types:
            seat_elem = block.find('span', string=lambda text: text and seat_type.lower() in text.lower())
            if seat_elem:
                # Извлекаем количество мест и цену
                parent = seat_elem.parent
                if parent:
                    count_elem = parent.find('span', class_='count') or parent.find('span', class_='places')
                    price_elem = parent.find('span', class_='price') or parent.find('span', class_='cost')
                    
                    count = count_elem.text.strip() if count_elem else '0'
                    price = price_elem.text.strip() if price_elem else '0'
                    
                    seats[seat_type] = {
                        'count': count,
                        'price': price
                    }
        
        return seats
    
    def _extract_prices(self, block) -> Dict:
        """
        Извлечение цен
        """
        prices = {}
        
        price_elements = block.find_all('span', class_='price') or block.find_all('span', class_='cost')
        
        for price_elem in price_elements:
            try:
                price_text = price_elem.text.strip()
                # Извлекаем числовое значение цены
                price_value = ''.join(filter(str.isdigit, price_text))
                if price_value:
                    prices[price_text] = int(price_value)
            except Exception as e:
                logger.warning(f"Ошибка извлечения цены: {e}")
                continue
        
        return prices
    
    def get_stations(self, query: str) -> List[Dict]:
        """
        Поиск станций по запросу
        """
        try:
            # URL для поиска станций
            stations_url = f"{self.base_url}/stations/search"
            
            params = {
                'query': query,
                'limit': 10
            }
            
            response = self.session.get(stations_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Парсим результаты поиска станций
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            
            stations = []
            if 'stations' in data:
                for station in data['stations']:
                    stations.append({
                        'code': station.get('code', ''),
                        'name': station.get('name', ''),
                        'region': station.get('region', '')
                    })
            
            return stations
            
        except Exception as e:
            logger.error(f"Ошибка поиска станций: {e}")
            return []

