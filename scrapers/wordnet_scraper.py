import nltk
import logging
from nltk.corpus import wordnet as wn

class WordNetScraper:
    def __init__(self):
        self.logger = logging.getLogger('wordnet_scraper')
        
        # Tải dữ liệu WordNet nếu chưa có
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            self.logger.info("Tải dữ liệu WordNet...")
            nltk.download('wordnet')
    
    def get_word_data(self, word):
        """Lấy dữ liệu từ từ WordNet"""
        result = {
            'word': word,
            'definitions': [],
            'examples': [],
            'synonyms': [],
            'antonyms': []
        }
        
        # Lấy các synset cho từ này
        synsets = wn.synsets(word)
        
        if not synsets:
            self.logger.warning(f"Không tìm thấy '{word}' trong WordNet")
            return None
            
        for synset in synsets:
            pos = self._convert_pos(synset.pos())
            
            # Lấy định nghĩa
            result['definitions'].append({
                'definition': synset.definition(),
                'pos': pos
            })
            
            # Lấy ví dụ
            for example in synset.examples():
                result['examples'].append({
                    'text': example,
                    'pos': pos
                })
            
            # Lấy từ đồng nghĩa và trái nghĩa
            for lemma in synset.lemmas():
                if lemma.name().lower() != word.lower():
                    result['synonyms'].append(lemma.name().replace('_', ' '))
                
                # Lấy từ trái nghĩa
                for antonym in lemma.antonyms():
                    result['antonyms'].append(antonym.name().replace('_', ' '))
        
        # Loại bỏ trùng lặp
        result['synonyms'] = list(set(result['synonyms']))
        result['antonyms'] = list(set(result['antonyms']))
        
        return result
    
    def _convert_pos(self, pos_code):
        """Chuyển đổi mã loại từ của WordNet sang dạng đầy đủ"""
        pos_map = {
            'n': 'noun',
            'v': 'verb',
            'a': 'adjective',
            's': 'adjective_satellite',
            'r': 'adverb'
        }
        return pos_map.get(pos_code, 'unknown')