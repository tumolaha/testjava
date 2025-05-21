import requests
import logging
import time
from bs4 import BeautifulSoup
import re

class VDictScraper:
    """Thu thập dữ liệu từ từ điển Anh-Việt trực tuyến"""
    
    def __init__(self):
        self.logger = logging.getLogger('vdict_scraper')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Dictionary Project/1.0 (educational project; contact@example.com)'
        })
        
    def get_word_data(self, word):
        """Thu thập dữ liệu từ các nguồn từ điển Anh-Việt online"""
        # Thử nhiều nguồn và kết hợp kết quả
        result = {
            'word': word,
            'pronunciations': [],
            'definitions': [],
            'examples': [],
            'synonyms': [],
            'antonyms': []
        }
        
        # Thu thập từ các nguồn khác nhau
        vdict_data = self._get_from_vdict(word)
        tracau_data = self._get_from_tracau(word)
        
        # Kết hợp dữ liệu
        if vdict_data:
            self._merge_data(result, vdict_data)
        
        if tracau_data:
            self._merge_data(result, tracau_data)
        
        # Nếu không tìm thấy dữ liệu từ bất kỳ nguồn nào
        if not result['definitions'] and not result['examples']:
            return None
            
        return result
    
    def _get_from_vdict(self, word):
        """Lấy dữ liệu từ VDict.com"""
        try:
            time.sleep(1)  # Tôn trọng giới hạn tốc độ
            url = f"https://vdict.com/{word},1,0,0.html"
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.logger.warning(f"Không thể kết nối đến VDict cho từ '{word}': {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                'word': word,
                'pronunciations': [],
                'definitions': [],
                'examples': []
            }
            
            # Lấy phát âm
            pron_div = soup.select_one('div.pronounce')
            if pron_div:
                pron_text = pron_div.get_text().strip()
                if pron_text:
                    result['pronunciations'].append(pron_text)
            
            # Lấy định nghĩa và ví dụ
            word_explain = soup.select_one('ul.list1')
            if word_explain:
                for li in word_explain.select('li'):
                    # Lấy loại từ và định nghĩa
                    content = li.get_text().strip()
                    if content:
                        # Cố gắng tách loại từ và định nghĩa
                        match = re.match(r'^(\w+)\s+(.+)$', content)
                        if match:
                            pos, definition = match.groups()
                            result['definitions'].append({
                                'definition': definition,
                                'definition_vi': definition,  # Đã là tiếng Việt rồi
                                'pos': pos
                            })
                        else:
                            result['definitions'].append({
                                'definition': content,
                                'definition_vi': content,  # Đã là tiếng Việt rồi
                                'pos': 'unknown'
                            })
                        
                        # Lấy ví dụ
                        examples_ul = li.select_one('ul.list2')
                        if examples_ul:
                            for ex_li in examples_ul.select('li'):
                                ex_text = ex_li.get_text().strip()
                                if ex_text:
                                    # Tách ví dụ tiếng Anh và tiếng Việt
                                    parts = ex_text.split(':', 1)
                                    if len(parts) == 2:
                                        en, vi = parts[0].strip(), parts[1].strip()
                                        result['examples'].append({
                                            'text': en,
                                            'text_vi': vi,
                                            'pos': pos if 'pos' in locals() else 'unknown'
                                        })
                                    else:
                                        result['examples'].append({
                                            'text': ex_text,
                                            'text_vi': '',
                                            'pos': pos if 'pos' in locals() else 'unknown'
                                        })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập từ VDict: {e}")
            return None
    
    def _get_from_tracau(self, word):
        """Lấy dữ liệu từ tra câu Lạc Việt"""
        try:
            time.sleep(1)  # Tôn trọng giới hạn tốc độ
            url = f"https://api.tracau.vn/WBBcwnwQpV89/s/{word}/en"
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.logger.warning(f"Không thể kết nối đến Tra câu cho từ '{word}': {response.status_code}")
                return None
                
            data = response.json()
            
            result = {
                'word': word,
                'pronunciations': [],
                'definitions': [],
                'examples': []
            }
            
            # Xử lý dữ liệu từ API traCau
            if 'tratu' in data:
                for item in data['tratu']:
                    if 'fields' in item and 'fulltext' in item['fields']:
                        soup = BeautifulSoup(item['fields']['fulltext'], 'html.parser')
                        
                        # Lấy phát âm
                        pron_span = soup.select_one('span.pronunciation')
                        if pron_span:
                            pron_text = pron_span.get_text().strip()
                            result['pronunciations'].append(pron_text)
                        
                        # Lấy định nghĩa
                        for meaning in soup.select('div.meaning-item'):
                            pos_span = meaning.select_one('span.widget-word-title')
                            pos = pos_span.get_text().strip() if pos_span else 'unknown'
                            
                            for meaning_li in meaning.select('li.meaning-defs'):
                                meaning_text = meaning_li.get_text().strip()
                                result['definitions'].append({
                                    'definition': word,  # Từ tiếng Anh
                                    'definition_vi': meaning_text,  # Định nghĩa tiếng Việt
                                    'pos': pos
                                })
                                
                                # Lấy ví dụ
                                for ex_div in meaning_li.select('div.example-item'):
                                    ex_en = ex_div.select_one('div.example-sentence')
                                    ex_vi = ex_div.select_one('div.example-sentence-meaning')
                                    
                                    if ex_en and ex_vi:
                                        result['examples'].append({
                                            'text': ex_en.get_text().strip(),
                                            'text_vi': ex_vi.get_text().strip(),
                                            'pos': pos
                                        })
            
            # Thu thập ví dụ từ các câu đã tra
            if 'sentences' in data and len(data['sentences']) > 0:
                for sent in data['sentences'][:5]:  # Giới hạn số lượng ví dụ
                    if 'fields' in sent:
                        en = sent['fields'].get('en', '')
                        vi = sent['fields'].get('vi', '')
                        
                        if en and vi:
                            result['examples'].append({
                                'text': en,
                                'text_vi': vi,
                                'pos': 'example'
                            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập từ Tra câu: {e}")
            return None
    
    def _merge_data(self, target, source):
        """Kết hợp dữ liệu từ nguồn mới vào kết quả hiện tại"""
        if not source:
            return
            
        # Kết hợp phát âm
        if 'pronunciations' in source and source['pronunciations']:
            for pron in source['pronunciations']:
                if pron not in target['pronunciations']:
                    target['pronunciations'].append(pron)
        
        # Kết hợp định nghĩa
        if 'definitions' in source and source['definitions']:
            for definition in source['definitions']:
                # Kiểm tra trùng lặp
                is_duplicate = False
                for existing_def in target['definitions']:
                    if (definition.get('definition_vi', '') == existing_def.get('definition_vi', '') and
                        definition.get('pos', '') == existing_def.get('pos', '')):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    target['definitions'].append(definition)
        
        # Kết hợp ví dụ
        if 'examples' in source and source['examples']:
            for example in source['examples']:
                # Kiểm tra trùng lặp
                is_duplicate = False
                for existing_ex in target['examples']:
                    if example.get('text', '') == existing_ex.get('text', ''):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    target['examples'].append(example)