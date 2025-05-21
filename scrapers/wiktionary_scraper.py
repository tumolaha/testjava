import requests
import logging
import time
from bs4 import BeautifulSoup

class WiktionaryScraper:
    def __init__(self):
        self.logger = logging.getLogger('wiktionary_scraper')
        self.base_url = "https://en.wiktionary.org/wiki/"
        self.api_url = "https://en.wiktionary.org/api/rest_v1/page/definition/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Dictionary Project/1.0 (educational project; contact@example.com)'
        })
        
    def get_word_data(self, word):
        """Lấy dữ liệu từ từ Wiktionary qua API"""
        try:
            time.sleep(1)  # Tôn trọng giới hạn tốc độ
            response = self.session.get(f"{self.api_url}{word}")
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_data(data, word)
            elif response.status_code == 404:
                self.logger.warning(f"Không tìm thấy '{word}' trong Wiktionary")
                return None
            else:
                self.logger.error(f"Lỗi API Wiktionary: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập từ Wiktionary: {e}")
            return None
    
    def get_word_data_html(self, word):
        """Lấy dữ liệu từ bằng cách phân tích HTML (fallback nếu API không hoạt động)"""
        try:
            time.sleep(1)  # Tôn trọng giới hạn tốc độ
            response = self.session.get(f"{self.base_url}{word}")
            
            if response.status_code == 200:
                return self._parse_html(response.text, word)
            else:
                self.logger.error(f"Lỗi tải trang Wiktionary: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập HTML từ Wiktionary: {e}")
            return None
    
    def _parse_api_data(self, data, word):
        """Phân tích dữ liệu trả về từ API Wiktionary"""
        result = {
            'word': word,
            'pronunciations': [],
            'definitions': [],
            'examples': []
        }
        
        if 'en' not in data:
            return result
            
        for entry in data['en']:
            # Lấy loại từ
            pos = entry.get('partOfSpeech', 'unknown')
            
            # Lấy định nghĩa
            for definition in entry.get('definitions', []):
                result['definitions'].append({
                    'definition': definition.get('definition', ''),
                    'pos': pos
                })
                
                # Lấy ví dụ
                for example in definition.get('examples', []):
                    result['examples'].append({
                        'text': example,
                        'pos': pos
                    })
        
        return result
    
    def _parse_html(self, html_content, word):
        """Phân tích HTML từ Wiktionary để trích xuất dữ liệu"""
        result = {
            'word': word,
            'pronunciations': [],
            'definitions': [],
            'examples': []
        }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tìm phần tiếng Anh
        english_section = None
        h2_elements = soup.find_all('h2')
        for h2 in h2_elements:
            if h2.find('span', id='English'):
                english_section = h2.find_next_sibling()
                break
        
        if not english_section:
            return result
            
        # Tìm phần phát âm
        pron_section = soup.find('span', id='Pronunciation')
        if pron_section:
            ul = pron_section.find_next('ul')
            if ul:
                for li in ul.find_all('li'):
                    ipa = li.find('span', class_='IPA')
                    if ipa:
                        result['pronunciations'].append(ipa.text.strip())
        
        # Tìm các định nghĩa theo loại từ
        current_pos = None
        h3_elements = soup.find_all('h3')
        for h3 in h3_elements:
            span = h3.find('span', class_='mw-headline')
            if span and h3.parent.name == 'body':  # Chỉ xem xét h3 trong phần tiếng Anh
                current_pos = span.text.strip()
                ol = h3.find_next('ol')
                if ol:
                    for li in ol.find_all('li', recursive=False):
                        definition = li.get_text().strip()
                        result['definitions'].append({
                            'definition': definition,
                            'pos': current_pos
                        })
                        
                        # Tìm ví dụ
                        examples_ul = li.find('ul')
                        if examples_ul:
                            for ex_li in examples_ul.find_all('li'):
                                example = ex_li.get_text().strip()
                                result['examples'].append({
                                    'text': example,
                                    'pos': current_pos
                                })
        
        return result