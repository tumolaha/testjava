import os
import logging
import struct
import gzip
import re
import sqlite3
from tqdm import tqdm

class StarDictAnhViet:
    def __init__(self, db_path='data/stardict/stardict_av.db', skip_sample=True):
        self.logger = logging.getLogger('stardict_anh_viet')
        self.db_path = db_path
        self.skip_sample = skip_sample
        self.setup_database()
    
    def setup_database(self):
        """Tạo cơ sở dữ liệu SQLite để lưu từ điển"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Tạo bảng từ điển
            c.execute('''
            CREATE TABLE IF NOT EXISTS dictionary (
                id INTEGER PRIMARY KEY,
                word TEXT NOT NULL,
                definition TEXT NOT NULL,
                source TEXT
            )
            ''')
            
            # Tạo các chỉ mục
            c.execute('CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Lỗi khi thiết lập cơ sở dữ liệu StarDict: {e}")
    
    def import_dict_file(self, dict_file, ifo_file=None, source_name="Anh-Viet"):
        """Nhập từ điển từ file .dict hoặc .dict.dz"""
        if not os.path.exists(dict_file):
            self.logger.error(f"File từ điển không tồn tại: {dict_file}")
            return False
        
        # Kiểm tra xem đây có phải là từ điển mẫu không
        if self.skip_sample and self._is_sample_dict(dict_file, source_name):
            self.logger.info(f"Bỏ qua từ điển mẫu: {source_name}")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Kiểm tra xem nguồn từ điển này đã được nhập chưa
            c.execute("SELECT COUNT(*) FROM dictionary WHERE source = ?", (source_name,))
            count = c.fetchone()[0]
            
            if count > 0:
                self.logger.info(f"Từ điển {source_name} đã được nhập ({count} từ). Đang bỏ qua.")
                conn.close()
                return True
            
            # Đọc file .ifo để lấy thông tin về số lượng từ (nếu có)
            word_count = 0
            if ifo_file and os.path.exists(ifo_file):
                with open(ifo_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.startswith('wordcount='):
                            word_count = int(line.split('=')[1].strip())
                            break
            
            # Đọc file .dict hoặc .dict.dz
            if dict_file.endswith('.dz'):
                with gzip.open(dict_file, 'rb') as f:
                    dict_content = f.read()
            else:
                with open(dict_file, 'rb') as f:
                    dict_content = f.read()
            
            # Xử lý nội dung từ điển
            offset = 0
            word_idx = 0
            
            # Sử dụng tqdm để hiển thị tiến trình
            progress_bar = None
            if word_count > 0:
                progress_bar = tqdm(total=word_count, desc=f"Importing {source_name}")
            
            # Bắt đầu transaction để tăng tốc độ
            c.execute("BEGIN TRANSACTION")
            
            while offset < len(dict_content):
                # Tìm ký tự kết thúc từ
                idx = dict_content.find(b'\0', offset)
                if idx == -1:
                    break
                
                # Lấy từ
                word = dict_content[offset:idx].decode('utf-8', errors='ignore')
                
                # Lấy độ dài định nghĩa
                if idx + 9 > len(dict_content):
                    break
                    
                definition_size = struct.unpack('>I', dict_content[idx+5:idx+9])[0]
                
                # Lấy định nghĩa
                start_def = idx + 9
                if start_def + definition_size > len(dict_content):
                    break
                    
                definition = dict_content[start_def:start_def+definition_size].decode('utf-8', errors='ignore')
                
                # Làm sạch định nghĩa (xóa tags HTML)
                definition = re.sub(r'<[^>]+>', ' ', definition)
                definition = re.sub(r'\s+', ' ', definition).strip()
                
                # Chỉ lưu các từ có nội dung hợp lệ
                if word and definition:
                    c.execute(
                        "INSERT INTO dictionary (word, definition, source) VALUES (?, ?, ?)",
                        (word, definition, source_name)
                    )
                    word_idx += 1
                
                # Cập nhật offset
                offset = start_def + definition_size
                
                # Cập nhật thanh tiến trình
                if progress_bar:
                    progress_bar.update(1)
            
            # Kết thúc thanh tiến trình
            if progress_bar:
                progress_bar.close()
            
            # Commit và đóng kết nối
            conn.commit()
            conn.close()
            
            self.logger.info(f"Đã nhập {word_idx} từ từ từ điển {source_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khi nhập từ điển StarDict: {e}")
            return False
    
    def _is_sample_dict(self, dict_file, source_name):
        """Kiểm tra xem đây có phải là từ điển mẫu không"""
        # Kiểm tra theo tên
        sample_patterns = ['sample', 'mẫu', 'test', 'simple', 'basic', 'local']
        if any(pattern in source_name.lower() for pattern in sample_patterns):
            return True
        
        # Kiểm tra kích thước file (từ điển mẫu thường rất nhỏ)
        try:
            file_size = os.path.getsize(dict_file)
            if file_size < 50000:  # Kích thước nhỏ hơn 50KB
                self.logger.info(f"Từ điển {source_name} có kích thước nhỏ ({file_size} bytes), có thể là từ điển mẫu")
                return True
        except:
            pass
        
        # Kiểm tra số lượng từ dựa trên file .ifo nếu có
        if os.path.exists(dict_file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo')):
            try:
                with open(dict_file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo'), 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Tìm wordcount
                    match = re.search(r'wordcount=(\d+)', content)
                    if match:
                        word_count = int(match.group(1))
                        if word_count < 100:  # Ít hơn 100 từ
                            self.logger.info(f"Từ điển {source_name} chỉ có {word_count} từ, có thể là từ điển mẫu")
                            return True
            except:
                pass
        
        return False
    
    def get_word_data(self, word):
        """Lấy dữ liệu từ và chuyển đổi sang định dạng chung"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Tìm kiếm chính xác
            c.execute("SELECT definition, source FROM dictionary WHERE word = ? LIMIT 10", (word,))
            results = c.fetchall()
            
            if not results:
                # Thử tìm kiếm không phân biệt chữ hoa/thường
                c.execute("SELECT definition, source FROM dictionary WHERE LOWER(word) = LOWER(?) LIMIT 10", (word,))
                results = c.fetchall()
                
                if not results:
                    conn.close()
                    return None
            
            # Kết quả trả về theo định dạng chung
            word_data = {
                'word': word,
                'pronunciations': [],
                'definitions': [],
                'examples': [],
                'sources': []
            }
            
            # Thu thập nguồn dữ liệu
            for _, source in results:
                if source not in word_data['sources']:
                    word_data['sources'].append(source)
            
            # Xử lý từng kết quả (có thể từ nhiều nguồn khác nhau)
            for definition_text, source in results:
                # Trích xuất phát âm
                pronunciation_patterns = [
                    r'/([^/]+)/',          # /pɹəˌnaʊnsiˈeɪʃən/
                    r'\[([^\]]+)\]',       # [pɹəˌnaʊnsiˈeɪʃən]
                    r'\/([^\/]+)\/',       # /pɹəˌnaʊnsiˈeɪʃən/
                    r'pronunciation: (.+)' # pronunciation: pɹəˌnaʊnsiˈeɪʃən
                ]
                
                for pattern in pronunciation_patterns:
                    pronunciation_match = re.search(pattern, definition_text)
                    if pronunciation_match:
                        pronunciation = pronunciation_match.group(1).strip()
                        if pronunciation and pronunciation not in word_data['pronunciations']:
                            word_data['pronunciations'].append(pronunciation)
                        break
                
                # Mẫu phân tích loại từ của StarDict Anh-Việt
                pos_patterns = [
                    r'\*(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)\*',
                    r'@(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)@',
                    r'<(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)>',
                    r'\[(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)\]',
                    r'\((danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)\)',
                    r'^(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ|từ hạn định|mạo từ)[,:\s]'
                ]
                
                # Thử từng mẫu pos_pattern cho đến khi tìm thấy
                pos_results = []
                for pos_pattern in pos_patterns:
                    pos_matches = list(re.finditer(pos_pattern, definition_text))
                    if pos_matches:
                        pos_results = pos_matches
                        break
                
                if pos_results:
                    # Tách định nghĩa theo loại từ
                    for i, match in enumerate(pos_results):
                        pos = match.group(1)
                        
                        # Lấy phần định nghĩa cho loại từ này
                        start_idx = match.end()
                        if i < len(pos_results) - 1:
                            end_idx = pos_results[i+1].start()
                            definition_part = definition_text[start_idx:end_idx].strip()
                        else:
                            definition_part = definition_text[start_idx:].strip()
                        
                        # Tách các nghĩa khác nhau
                        # Các dấu hiệu phân tách nghĩa: ";", "◦", "•", "·", "※"
                        meanings = re.split(r';|◦|•|·|※|,(?![^(]*\))', definition_part)
                        
                        for meaning in meanings:
                            meaning = meaning.strip()
                            if meaning:
                                # Tách phần ví dụ (thường nằm sau dấu hai chấm, dấu "=>", "Ex:", "VD:")
                                examples_markers = [': ', ' => ', 'Ex: ', 'VD: ', 'e.g. ', 'Ex. ']
                                examples = []
                                pure_meaning = meaning
                                
                                for marker in examples_markers:
                                    if marker in meaning:
                                        parts = meaning.split(marker, 1)
                                        pure_meaning = parts[0].strip()
                                        if len(parts) > 1:
                                            examples_text = parts[1]
                                            # Tách nhiều ví dụ
                                            example_items = re.split(r';|\|', examples_text)
                                            examples.extend([ex.strip() for ex in example_items if ex.strip()])
                                        break
                                
                                # Thêm định nghĩa
                                word_data['definitions'].append({
                                    'definition': word,  # Từ tiếng Anh
                                    'definition_vi': pure_meaning,  # Nghĩa tiếng Việt
                                    'pos': self._convert_pos_to_english(pos),
                                    'source': source
                                })
                                
                                # Xử lý ví dụ
                                for example in examples:
                                    # Tách ví dụ tiếng Anh và nghĩa tiếng Việt
                                    # Các dấu hiệu phân tách: "-", ":", "=", "→"
                                    example_parts = re.split(r'\s+-\s+|\s*:\s*|\s*=\s*|\s*→\s*', example, 1)
                                    
                                    if len(example_parts) > 1:
                                        ex_en, ex_vi = example_parts[0].strip(), example_parts[1].strip()
                                    else:
                                        # Nếu không thể tách, giả định là ví dụ tiếng Anh
                                        ex_en, ex_vi = example.strip(), ""
                                    
                                    # Thêm ví dụ
                                    if ex_en:
                                        word_data['examples'].append({
                                            'text': ex_en,
                                            'text_vi': ex_vi,
                                            'pos': self._convert_pos_to_english(pos),
                                            'source': source
                                        })
                else:
                    # Không tìm thấy loại từ theo mẫu, thử cách khác
                    
                    # Loại bỏ phần phát âm nếu có
                    for pattern in pronunciation_patterns:
                        definition_text = re.sub(pattern, '', definition_text)
                    
                    # Kiểm tra từ "danh từ", "động từ", v.v. trong văn bản
                    pos_simple = re.search(r'(danh từ|tính từ|động từ|trạng từ|giới từ|liên từ|đại từ|thán từ)', definition_text)
                    if pos_simple:
                        pos = pos_simple.group(1)
                        # Lấy phần sau loại từ
                        definition_part = definition_text[pos_simple.end():].strip()
                        
                        word_data['definitions'].append({
                            'definition': word,
                            'definition_vi': definition_part,
                            'pos': self._convert_pos_to_english(pos),
                            'source': source
                        })
                    else:
                        # Nếu không tìm thấy loại từ, thêm toàn bộ định nghĩa
                        word_data['definitions'].append({
                            'definition': word,
                            'definition_vi': definition_text,
                            'pos': 'unknown',
                            'source': source
                        })
            
            conn.close()
            
            # Loại bỏ các định nghĩa trùng lặp
            unique_defs = []
            seen_defs = set()
            
            for definition in word_data['definitions']:
                def_key = (definition['pos'], definition['definition_vi'])
                if def_key not in seen_defs:
                    unique_defs.append(definition)
                    seen_defs.add(def_key)
            
            word_data['definitions'] = unique_defs
            
            # Loại bỏ các ví dụ trùng lặp
            unique_examples = []
            seen_examples = set()
            
            for example in word_data['examples']:
                ex_key = (example['text'], example['text_vi'])
                if ex_key not in seen_examples:
                    unique_examples.append(example)
                    seen_examples.add(ex_key)
            
            word_data['examples'] = unique_examples
            
            return word_data
                
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm từ trong StarDict: {e}")
            if 'conn' in locals():
                conn.close()
            return None
    
    def _convert_pos_to_english(self, vietnamese_pos):
        """Chuyển đổi loại từ từ tiếng Việt sang tiếng Anh"""
        pos_map = {
            'danh từ': 'noun',
            'tính từ': 'adjective',
            'động từ': 'verb',
            'trạng từ': 'adverb',
            'giới từ': 'preposition',
            'liên từ': 'conjunction',
            'đại từ': 'pronoun',
            'thán từ': 'interjection',
            'từ hạn định': 'determiner',
            'mạo từ': 'article'
        }
        return pos_map.get(vietnamese_pos, 'unknown')