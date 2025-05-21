import requests
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv()

class VietnameseTranslator:
    def __init__(self):
        self.logger = logging.getLogger('vietnamese_translator')
        # Có thể sử dụng dịch vụ Google Translate hoặc dịch vụ khác với API key
        # Ví dụ này sử dụng MyMemory Translation API (miễn phí với giới hạn)
        self.base_url = "https://api.mymemory.translated.net/get"
    
    def translate_definition(self, text, retry_count=3):
        """Dịch định nghĩa sang tiếng Việt"""
        if not text:
            return ""
            
        try:
            # Tôn trọng giới hạn tốc độ
            time.sleep(1)
            
            params = {
                'q': text,
                'langpair': 'en|vi',
                'de': 'your-email@example.com'  # Thêm email để tăng giới hạn
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('responseStatus') == 200:
                    return data.get('responseData', {}).get('translatedText', '')
                else:
                    self.logger.warning(f"Lỗi dịch: {data.get('responseStatus')} - {data.get('responseDetails')}")
                    if retry_count > 0 and 'MYMEMORY USAGE LIMIT' in data.get('responseDetails', ''):
                        self.logger.info(f"Đang thử lại sau 5 giây... (còn {retry_count} lần)")
                        time.sleep(5)
                        return self.translate_definition(text, retry_count - 1)
                    return ""
            else:
                self.logger.error(f"HTTP Error: {response.status_code}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Lỗi khi dịch: {e}")
            return ""
    
    def translate_example(self, example):
        """Dịch ví dụ sang tiếng Việt"""
        return self.translate_definition(example)
    
    def post_process_translation(self, text):
        """Xử lý sau dịch để cải thiện chất lượng bản dịch"""
        # Một số hậu xử lý đơn giản
        text = text.replace('&#39;', "'")
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        
        # Có thể thêm các quy tắc điều chỉnh bản dịch khác
        
        return text