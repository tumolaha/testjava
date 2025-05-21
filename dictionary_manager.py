import logging
import os
import time
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import glob
import sqlite3

# Import các lớp
from database.db_connector import DatabaseConnector
from scrapers.wordnet_scraper import WordNetScraper
from scrapers.wiktionary_scraper import WiktionaryScraper
from scrapers.oxford_scraper import OxfordDictionaryScraper
from translators.vietnamese_translator import VietnameseTranslator
from scrapers.vdict_scraper import VDictScraper
from scrapers.stardict_anh_viet import StarDictAnhViet

class DictionaryManager:
    def __init__(self):
        # Thiết lập logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=f'logs/dictionary_manager_{datetime.now().strftime("%Y%m%d")}.log',
            filemode='a'
        )
        self.logger = logging.getLogger('dictionary_manager')
        
        # Khởi tạo các thành phần
        self.db = DatabaseConnector()
        self.wordnet = WordNetScraper()
        self.wiktionary = WiktionaryScraper()
        self.oxford = OxfordDictionaryScraper()
        self.translator = VietnameseTranslator()
        self.vdict = VDictScraper()
        
        # Tạo thư mục dữ liệu nếu chưa tồn tại
        os.makedirs('data/dictionaries', exist_ok=True)
        
        # Khởi tạo StarDict Anh-Việt với các nguồn từ điển đã tải
        self.stardict_sources = self._load_available_dictionaries()
        self.stardict_av = StarDictAnhViet()
        
        # Nạp tự động tất cả các nguồn từ điển có sẵn
        if self.stardict_sources:
            for source in self.stardict_sources:
                self.logger.info(f"Khởi tạo từ điển: {source['name']}")
                if self.stardict_av.import_dict_file(source['dict'], source['ifo'], source['name']):
                    self.logger.info(f"Đã nạp từ điển {source['name']} thành công")
                else:
                    self.logger.warning(f"Không thể nạp từ điển {source['name']}")
        else:
            self.logger.warning("Không tìm thấy file từ điển nào trong thư mục data/dictionaries hoặc data/stardict")
            self.logger.warning("LƯU Ý QUAN TRỌNG: Việc thu thập dữ liệu sẽ không có kết quả tốt nếu không có từ điển Anh-Việt")
            self.logger.warning("Vui lòng chạy lệnh sau để tải từ điển: python main.py --download")
            self.logger.warning("Hoặc tải thủ công từ điển và đặt vào thư mục data/dictionaries")
            
            # Thử tìm trong thư mục data/stardict (tương thích với phiên bản cũ)
            if os.path.exists('data/stardict'):
                stardict_files = glob.glob('data/stardict/*.dict*')
                if stardict_files:
                    for dict_file in stardict_files:
                        name = os.path.basename(dict_file).split('.')[0]
                        ifo_file = dict_file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo')
                        if os.path.exists(ifo_file):
                            self.logger.info(f"Tìm thấy từ điển cũ: {name}")
                            if self.stardict_av.import_dict_file(dict_file, ifo_file, name):
                                self.logger.info(f"Đã nạp từ điển {name} thành công")
        
        # Kết nối đến cơ sở dữ liệu
        if not self.db.connect():
            self.logger.error("Không thể kết nối đến cơ sở dữ liệu. Đang thoát.")
            raise ConnectionError("Database connection failed")
    
    def _load_available_dictionaries(self):
        """Tải tất cả các từ điển có sẵn từ thư mục data/dictionaries"""
        sources = []
        
        # Kiểm tra thư mục chính
        if not os.path.exists('data/dictionaries'):
            self.logger.warning("Thư mục data/dictionaries không tồn tại")
            return sources
        
        # Tìm tất cả các file .dict và .dict.dz
        dict_files = glob.glob('data/dictionaries/*.dict*')
        
        for dict_file in dict_files:
            name = os.path.basename(dict_file).split('.')[0]
            ifo_file = dict_file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo')
            
            sources.append({
                'name': name,
                'dict': dict_file,
                'ifo': ifo_file if os.path.exists(ifo_file) else None
            })
        
        self.logger.info(f"Đã tìm thấy {len(sources)} nguồn từ điển")
        return sources

    # Thêm phương thức mới để lọc các nguồn từ điển

    def filter_dictionary_sources(self, sources):
        """Lọc bỏ các nguồn từ điển không chính thức hoặc mẫu"""
        filtered_sources = []
        
        # Danh sách các nguồn từ điển mẫu cần loại bỏ
        sample_dict_patterns = [
            'sample', 'mẫu', 'test', 'simple', 'basic', 'local'
        ]
        
        for source in sources:
            source_name = source.get('name', '').lower()
            is_sample = any(pattern in source_name for pattern in sample_dict_patterns)
            
            if not is_sample:
                filtered_sources.append(source)
            else:
                self.logger.info(f"Đã loại bỏ nguồn từ điển mẫu: {source.get('name')}")
        
        return filtered_sources

    def process_word(self, word):
        """Xử lý một từ và lưu vào cơ sở dữ liệu"""
        self.logger.info(f"Đang xử lý từ: {word}")
        
        # Kiểm tra xem từ đã tồn tại chưa
        word_id = self.db.word_exists(word)
        if word_id:
            self.logger.info(f"Từ '{word}' đã tồn tại với ID {word_id}")
            return word_id
        
        # Thu thập dữ liệu từ các nguồn, ưu tiên từ điển Anh-Việt
        data_sources = {}
        
        # 1. Thu thập từ StarDict Anh-Việt (nguồn đáng tin cậy nhất)
        if self.stardict_av:
            data_sources['stardict_av'] = self.stardict_av.get_word_data(word)
        
        # 2. Thu thập từ dịch vụ từ điển Anh-Việt trực tuyến
        data_sources['vdict'] = self.vdict.get_word_data(word)
        
        # 3. Thu thập từ các nguồn tiếng Anh chỉ khi không có dữ liệu Anh-Việt
        if not data_sources['stardict_av'] and not data_sources['vdict']:
            data_sources['oxford'] = self.oxford.get_word_data(word)
            data_sources['wordnet'] = self.wordnet.get_word_data(word)
            data_sources['wiktionary'] = self.wiktionary.get_word_data(word)
        
        # Kết hợp dữ liệu, ưu tiên nguồn Anh-Việt
        combined_data = self._combine_data_prioritizing_vi(word, data_sources)
        
        if not combined_data:
            self.logger.warning(f"Không tìm thấy dữ liệu cho '{word}' từ bất kỳ nguồn nào")
            return None
        
        # Lưu dữ liệu vào cơ sở dữ liệu
        return self._save_word_to_database(combined_data)
    
    def _combine_data_prioritizing_vi(self, word, data_sources):
        """Kết hợp dữ liệu từ các nguồn khác nhau, ưu tiên dữ liệu Anh-Việt"""
        result = {
            'word': word,
            'pronunciations': [],
            'definitions': [],
            'examples': [],
            'synonyms': [],
            'antonyms': [],
            'etymologies': []
        }
        
        # Kiểm tra xem có dữ liệu từ bất kỳ nguồn nào không
        if not any(data_sources.values()):
            return None
        
        # Ưu tiên 1: Dữ liệu StarDict Anh-Việt
        if data_sources.get('stardict_av'):
            stardict_data = data_sources['stardict_av']
            
            # Lấy phát âm
            if stardict_data.get('pronunciations'):
                result['pronunciations'].extend(stardict_data['pronunciations'])
            
            # Lấy định nghĩa
            if stardict_data.get('definitions'):
                for definition in stardict_data['definitions']:
                    result['definitions'].append(definition)
            
            # Lấy ví dụ
            if stardict_data.get('examples'):
                for example in stardict_data['examples']:
                    result['examples'].append(example)
        
        # Ưu tiên 2: Dữ liệu VDict hoặc Tra câu
        if data_sources.get('vdict'):
            vdict_data = data_sources['vdict']
            
            # Thêm phát âm nếu chưa có
            if not result['pronunciations'] and vdict_data.get('pronunciations'):
                result['pronunciations'].extend(vdict_data['pronunciations'])
            
            # Thêm định nghĩa từ VDict
            if vdict_data.get('definitions'):
                # Ghi lại các loại từ đã có
                existing_pos = {d.get('pos'): True for d in result['definitions']}
                
                for definition in vdict_data['definitions']:
                    pos = definition.get('pos', 'unknown')
                    
                    # Thêm vào nếu chưa có loại từ này
                    if pos not in existing_pos:
                        result['definitions'].append(definition)
                        existing_pos[pos] = True
            
            # Thêm ví dụ từ VDict
            if vdict_data.get('examples'):
                # Ghi lại các ví dụ đã có
                existing_examples = {ex.get('text', ''): True for ex in result['examples']}
                
                for example in vdict_data['examples']:
                    example_text = example.get('text', '')
                    
                    # Thêm ví dụ nếu chưa có
                    if example_text and example_text not in existing_examples:
                        result['examples'].append(example)
                        existing_examples[example_text] = True
        
        # Ưu tiên 3: Dữ liệu tiếng Anh khác nếu không có Anh-Việt
        if not result['definitions']:
            for source_name in ['oxford', 'wordnet', 'wiktionary']:
                source_data = data_sources.get(source_name)
                if not source_data:
                    continue
                    
                # Ghi lại các loại từ đã có
                existing_pos = {d.get('pos'): True for d in result['definitions']}
                
                # Lấy phát âm nếu chưa có
                if not result['pronunciations'] and source_data.get('pronunciations'):
                    result['pronunciations'].extend(source_data['pronunciations'])
                
                # Lấy định nghĩa
                if source_data.get('definitions'):
                    for definition in source_data['definitions']:
                        pos = definition.get('pos', 'unknown')
                        
                        # Nếu loại từ này chưa có, thêm vào
                        if pos not in existing_pos:
                            # Nếu là nguồn tiếng Anh, cần dịch sang tiếng Việt
                            definition_en = definition.get('definition', '')
                            if 'definition_vi' not in definition or not definition['definition_vi']:
                                definition['definition_vi'] = self.translator.translate_definition(definition_en)
                            
                            result['definitions'].append(definition)
                            existing_pos[pos] = True
                
                # Lấy ví dụ
                if source_data.get('examples'):
                    # Ghi lại các ví dụ đã có
                    existing_examples = {ex.get('text', ''): True for ex in result['examples']}
                    
                    for example in source_data['examples']:
                        example_text = example.get('text', '')
                        
                        # Thêm ví dụ nếu chưa có
                        if example_text and example_text not in existing_examples:
                            # Dịch ví dụ nếu chưa có bản dịch
                            if 'text_vi' not in example or not example['text_vi']:
                                example['text_vi'] = self.translator.translate_example(example_text)
                            
                            result['examples'].append(example)
                            existing_examples[example_text] = True
        
        # Kết hợp từ đồng nghĩa và trái nghĩa từ WordNet
        wordnet_data = data_sources.get('wordnet')
        if wordnet_data:
            if 'synonyms' in wordnet_data and wordnet_data['synonyms']:
                result['synonyms'].extend(wordnet_data['synonyms'])
            if 'antonyms' in wordnet_data and wordnet_data['antonyms']:
                result['antonyms'].extend(wordnet_data['antonyms'])
        
        # Loại bỏ trùng lặp
        result['synonyms'] = list(set(result['synonyms']))
        result['antonyms'] = list(set(result['antonyms']))
        
        return result
    
    def _save_word_to_database(self, data):
        """Lưu dữ liệu từ vào cơ sở dữ liệu"""
        word = data['word']
        
        # Lấy phát âm
        pronunciation = ""
        if data['pronunciations']:
            if isinstance(data['pronunciations'][0], dict):
                pronunciation = data['pronunciations'][0].get('text', '')
            else:
                pronunciation = data['pronunciations'][0]
        
        # Thêm từ vào bảng words
        word_id = self.db.insert_word(word, pronunciation)
        if not word_id:
            self.logger.error(f"Không thể thêm từ '{word}' vào cơ sở dữ liệu")
            return None
        
        # Thêm định nghĩa
        for definition in data['definitions']:
            # Lấy định nghĩa tiếng Anh và tiếng Việt
            definition_en = definition.get('definition', '')
            definition_vi = definition.get('definition_vi', '')
            
            # Nếu không có định nghĩa tiếng Việt, dịch từ tiếng Anh
            if not definition_vi and definition_en:
                definition_vi = self.translator.translate_definition(definition_en)
                definition_vi = self.translator.post_process_translation(definition_vi)
            
            # Lấy hoặc thêm loại từ
            pos = definition.get('pos', 'unknown')
            pos_id = self._get_or_create_pos(pos)
            
            # Thêm định nghĩa
            definition_id = self._add_definition(word_id, pos_id, definition_en, definition_vi)
            
            if not definition_id:
                continue
                
            # Thêm ví dụ cho định nghĩa này
            examples_for_pos = [ex for ex in data.get('examples', []) if ex.get('pos', '') == pos]
            for example in examples_for_pos:
                example_en = example.get('text', '')
                example_vi = example.get('text_vi', '')
                
                # Nếu không có bản dịch ví dụ, dịch từ tiếng Anh
                if not example_vi and example_en:
                    example_vi = self.translator.translate_example(example_en)
                    example_vi = self.translator.post_process_translation(example_vi)
                
                # Thêm ví dụ
                if example_en:
                    query = """
                    INSERT INTO examples 
                    (word_definition_id, example_en, example_vi, source) 
                    VALUES (%s, %s, %s, %s)
                    """
                    self.db.execute_query(
                        query, 
                        (definition_id, example_en, example_vi, 'combined')
                    )
        
        # Thêm từ đồng nghĩa và trái nghĩa
        self._add_synonyms_antonyms(word_id, data.get('synonyms', []), data.get('antonyms', []))
        
        self.logger.info(f"Đã lưu từ '{word}' với ID {word_id}")
        return word_id
    
    def _get_or_create_pos(self, pos_name):
        """Lấy ID loại từ hoặc tạo mới nếu chưa tồn tại"""
        query = "SELECT id FROM parts_of_speech WHERE name = %s"
        result = self.db.execute_and_fetchone(query, (pos_name,))
        
        if result:
            return result[0]
        
        # Tạo mới nếu chưa tồn tại
        query = "INSERT INTO parts_of_speech (name) VALUES (%s) RETURNING id"
        result = self.db.execute_and_fetchone(query, (pos_name,))
        
        if result:
            return result[0]
        return None
    
    def _add_definition(self, word_id, pos_id, definition_en, definition_vi):
        """Thêm định nghĩa vào cơ sở dữ liệu"""
        query = """
        INSERT INTO word_definitions 
        (word_id, part_of_speech_id, definition_en, definition_vi, source) 
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.db.execute_and_fetchone(
            query, 
            (word_id, pos_id, definition_en, definition_vi, 'combined')
        )
        
        if result:
            return result[0]
        return None
    
    def _add_examples_for_definition(self, definition_id, examples, pos):
        """Thêm ví dụ cho định nghĩa"""
        # Lọc ví dụ cho loại từ này
        filtered_examples = [ex for ex in examples if ex.get('pos', '') == pos]
        
        for example in filtered_examples:
            example_text = example.get('text', '')
            if not example_text:
                continue
                
            # Dịch ví dụ sang tiếng Việt
            example_vi = self.translator.translate_example(example_text)
            example_vi = self.translator.post_process_translation(example_vi)
            
            # Thêm ví dụ
            query = """
            INSERT INTO examples 
            (word_definition_id, example_en, example_vi, source) 
            VALUES (%s, %s, %s, %s)
            """
            self.db.execute_query(
                query, 
                (definition_id, example_text, example_vi, 'combined')
            )
    
    def _add_synonyms_antonyms(self, word_id, synonyms, antonyms):
        """Thêm từ đồng nghĩa và trái nghĩa"""
        # Thêm từ đồng nghĩa
        for synonym in synonyms:
            # Kiểm tra hoặc thêm từ đồng nghĩa
            synonym_id = self.db.word_exists(synonym)
            if not synonym_id:
                # Xử lý từ đồng nghĩa nếu chưa tồn tại
                synonym_id = self.db.insert_word(synonym, '')
            
            if synonym_id:
                # Lấy định nghĩa đầu tiên của từ hiện tại
                query = "SELECT id FROM word_definitions WHERE word_id = %s LIMIT 1"
                result = self.db.execute_and_fetchone(query, (word_id,))
                
                if result:
                    definition_id = result[0]
                    # Thêm mối quan hệ đồng nghĩa
                    query = """
                    INSERT INTO synonyms (word_definition_id, synonym_word_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """
                    self.db.execute_query(query, (definition_id, synonym_id))
        
        # Thêm từ trái nghĩa (tương tự)
        for antonym in antonyms:
            antonym_id = self.db.word_exists(antonym)
            if not antonym_id:
                antonym_id = self.db.insert_word(antonym, '')
            
            if antonym_id:
                query = "SELECT id FROM word_definitions WHERE word_id = %s LIMIT 1"
                result = self.db.execute_and_fetchone(query, (word_id,))
                
                if result:
                    definition_id = result[0]
                    query = """
                    INSERT INTO antonyms (word_definition_id, antonym_word_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """
                    self.db.execute_query(query, (definition_id, antonym_id))
    
    def process_word_list(self, word_list, batch_size=100):
        """Xử lý một danh sách từ"""
        total = len(word_list)
        self.logger.info(f"Bắt đầu xử lý {total} từ")
        
        results = []
        
        for i in tqdm(range(0, total, batch_size)):
            batch = word_list[i:i+batch_size]
            
            for word in batch:
                word_id = self.process_word(word.strip())
                results.append((word, word_id is not None))
            
            # Sau mỗi batch, xuất báo cáo
            self._report_progress(results)
            
            # Sau mỗi batch, tạm dừng để không tạo quá nhiều requests
            if i + batch_size < total:
                time.sleep(5)
        
        return results
    
    def process_word_file(self, file_path, batch_size=100):
        """Xử lý danh sách từ từ file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            return self.process_word_list(words, batch_size)
            
        except Exception as e:
            self.logger.error(f"Lỗi khi đọc file {file_path}: {e}")
            return []
    
    def _report_progress(self, results):
        """Báo cáo tiến trình xử lý"""
        total = len(results)
        successful = sum(1 for _, success in results if success)
        
        self.logger.info(f"Tiến trình: {successful}/{total} từ thành công ({successful/total*100:.2f}%)")
    
    def export_to_sql(self, output_file):
        """Xuất cơ sở dữ liệu thành file SQL"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_file}_{timestamp}.sql"
        
        success = self.db.export_to_sql(filename)
        
        if success:
            self.logger.info(f"Đã xuất cơ sở dữ liệu thành công ra {filename}")
        else:
            self.logger.error(f"Xuất cơ sở dữ liệu thất bại")
        
        return success, filename
    
    def close(self):
        """Đóng kết nối và dọn dẹp tài nguyên"""
        self.db.disconnect()
        self.logger.info("Đã đóng tất cả kết nối")
    
    # Thêm phương thức kiểm tra và cảnh báo

    def check_dictionary_quality(self):
        """Kiểm tra chất lượng từ điển và cảnh báo nếu chỉ có từ điển mẫu"""
        if not hasattr(self, 'stardict_av') or not self.stardict_av:
            self.logger.warning("Không có từ điển StarDict được nạp")
            return False
        
        # Kiểm tra số lượng từ trong cơ sở dữ liệu
        try:
            conn = sqlite3.connect(self.stardict_av.db_path)
            c = conn.cursor()
            
            # Đếm tổng số từ
            c.execute("SELECT COUNT(*) FROM dictionary")
            total_count = c.fetchone()[0]
            
            # Đếm số nguồn từ điển
            c.execute("SELECT COUNT(DISTINCT source) FROM dictionary")
            source_count = c.fetchone()[0]
            
            # Lấy danh sách nguồn
            c.execute("SELECT source, COUNT(*) FROM dictionary GROUP BY source")
            sources = c.fetchall()
            
            conn.close()
            
            # Kiểm tra số lượng từ quá ít
            if total_count < 100:
                self.logger.warning(f"Từ điển hiện có rất ít từ ({total_count}), có thể là từ điển mẫu.")
                self.logger.warning("Kết quả thu thập dữ liệu có thể không chính xác.")
                return False
            
            # Kiểm tra các nguồn mẫu
            sample_sources = []
            for source, count in sources:
                if any(pattern in source.lower() for pattern in ['sample', 'mẫu', 'test', 'simple', 'basic']):
                    sample_sources.append((source, count))
            
            if sample_sources and source_count <= len(sample_sources):
                self.logger.warning("Chỉ có từ điển mẫu được nạp:")
                for source, count in sample_sources:
                    self.logger.warning(f"  - {source}: {count} từ")
                self.logger.warning("Vui lòng tải xuống từ điển chính thức để có kết quả chính xác hơn:")
                self.logger.warning("  python main.py --download")
                return False
            
            if sample_sources:
                self.logger.info("Có cả từ điển mẫu và chính thức. Hệ thống sẽ ưu tiên nguồn chính thức.")
            else:
                self.logger.info(f"Từ điển đủ chất lượng: {total_count} từ từ {source_count} nguồn.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khi kiểm tra chất lượng từ điển: {e}")
            return False
