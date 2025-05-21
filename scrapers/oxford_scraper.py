import requests
import logging
import os
import time
from dotenv import load_dotenv

load_dotenv()

class OxfordDictionaryScraper:
    def __init__(self):
        self.logger = logging.getLogger('oxford_scraper')
        self.app_id = os.getenv('OXFORD_DICT_APP_ID')
        self.app_key = os.getenv('OXFORD_DICT_APP_KEY')
        
        if not self.app_id or not self.app_key:
            self.logger.warning("Thiếu thông tin xác thực Oxford Dictionary API")
        
        self.base_url = "https://od-api.oxforddictionaries.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def get_word_data(self, word):
        """Lấy dữ liệu từ từ Oxford Dictionary API"""
        if not self.app_id or not self.app_key:
            self.logger.warning("API key for Oxford Dictionary not configured - skipping this source")
            return None
            
        try:
            # Tôn trọng giới hạn tốc độ
            time.sleep(1)
            
            # Tìm kiếm từ
            endpoint = f"/entries/en-gb/{word.lower()}"
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 200:
                return self._parse_response(response.json(), word)
            elif response.status_code == 403:
                self.logger.error(f"Lỗi xác thực Oxford API - Oxford Dictionary data will not be available")
                # Set keys to None so we don't keep trying
                self.app_id = None
                self.app_key = None
                return None
            elif response.status_code == 404:
                self.logger.warning(f"Không tìm thấy '{word}' trong Oxford Dictionary")
                return None
            else:
                self.logger.error(f"Lỗi Oxford API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập từ Oxford Dictionary: {e}")
            return None
    
    def _parse_response(self, data, word):
        """Phân tích dữ liệu từ Oxford Dictionary API"""
        result = {
            'word': word,
            'pronunciations': [],
            'definitions': [],
            'examples': [],
            'etymologies': []
        }
        
        try:
            lexical_entries = data.get('results', [{}])[0].get('lexicalEntries', [])
            
            for entry in lexical_entries:
                # Lấy loại từ
                pos = entry.get('lexicalCategory', {}).get('text', 'unknown')
                
                # Lấy phát âm
                entries = entry.get('entries', [])
                for e in entries:
                    # Lấy phát âm
                    for pronunciation in e.get('pronunciations', []):
                        if 'phoneticSpelling' in pronunciation:
                            result['pronunciations'].append({
                                'text': pronunciation.get('phoneticSpelling'),
                                'audio': pronunciation.get('audioFile', '')
                            })
                    
                    # Lấy từ nguyên
                    for etymology in e.get('etymologies', []):
                        result['etymologies'].append(etymology)
                    
                    # Lấy nghĩa và ví dụ
                    senses = e.get('senses', [])
                    for sense in senses:
                        # Lấy định nghĩa
                        for definition in sense.get('definitions', []):
                            result['definitions'].append({
                                'definition': definition,
                                'pos': pos,
                                'domains': [d.get('text') for d in sense.get('domains', [])]
                            })
                        
                        # Lấy ví dụ
                        for example in sense.get('examples', []):
                            result['examples'].append({
                                'text': example.get('text', ''),
                                'pos': pos
                            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Lỗi khi phân tích dữ liệu Oxford: {e}")
            return result