import sqlite3
import logging
from tqdm import tqdm
from config import DB_PATH

class DictionaryDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.setup_tables()
    
    def connect(self):
        """Kết nối đến database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            raise
    
    def setup_tables(self):
        """Tạo bảng nếu chưa tồn tại"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS english_vietnamese (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_word VARCHAR(255) NOT NULL,
            vietnamese_meaning TEXT NOT NULL,
            word_type VARCHAR(50),
            pronunciation VARCHAR(255),
            example TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS vietnamese_english (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vietnamese_word VARCHAR(255) NOT NULL,
            english_meaning TEXT NOT NULL,
            word_type VARCHAR(50),
            example TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_english_word ON english_vietnamese(english_word);
        CREATE INDEX IF NOT EXISTS idx_vietnamese_word ON vietnamese_english(vietnamese_word);
        """
        try:
            self.cursor.executescript(schema_sql)
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error setting up tables: {e}")
            raise
    
    def batch_insert_en_vi(self, entries, batch_size=1000):
        """Chèn các mục Anh-Việt theo lô"""
        if not entries:
            return 0
        
        count = 0
        try:
            # Xử lý theo lô để tránh vấn đề bộ nhớ
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i+batch_size]
                
                # Chuẩn bị dữ liệu để chèn
                values = [(
                    entry['english_word'], 
                    entry['vietnamese_meaning'], 
                    entry.get('word_type', ''), 
                    entry.get('pronunciation', ''), 
                    entry.get('example', '')
                ) for entry in batch]
                
                # Sử dụng executemany với IGNORE để bỏ qua bản ghi trùng lặp
                self.cursor.executemany(
                    """INSERT OR IGNORE INTO english_vietnamese 
                       (english_word, vietnamese_meaning, word_type, pronunciation, example) 
                       VALUES (?, ?, ?, ?, ?)""",
                    values
                )
                self.conn.commit()
                count += len(batch)
        
        except Exception as e:
            logging.error(f"Error batch inserting into english_vietnamese: {e}")
            raise
        
        return count
    
    def batch_insert_vi_en(self, entries, batch_size=1000):
        """Chèn các mục Việt-Anh theo lô"""
        if not entries:
            return 0
        
        count = 0
        try:
            # Xử lý theo lô để tránh vấn đề bộ nhớ
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i+batch_size]
                
                # Chuẩn bị dữ liệu để chèn
                values = [(
                    entry['vietnamese_word'], 
                    entry['english_meaning'], 
                    entry.get('word_type', ''), 
                    entry.get('example', '')
                ) for entry in batch]
                
                # Sử dụng executemany với IGNORE để bỏ qua bản ghi trùng lặp
                self.cursor.executemany(
                    """INSERT OR IGNORE INTO vietnamese_english 
                       (vietnamese_word, english_meaning, word_type, example) 
                       VALUES (?, ?, ?, ?)""",
                    values
                )
                self.conn.commit()
                count += len(batch)
        
        except Exception as e:
            logging.error(f"Error batch inserting into vietnamese_english: {e}")
            raise
        
        return count
    
    def remove_duplicates(self):
        """Xóa các mục trùng lặp từ cơ sở dữ liệu"""
        print("Removing duplicate entries...")
        
        try:
            # Xử lý trùng lặp Anh-Việt
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS english_vietnamese_temp AS
                SELECT MIN(id) as id, english_word, vietnamese_meaning, word_type, pronunciation, example
                FROM english_vietnamese
                GROUP BY english_word, vietnamese_meaning
            """)
            
            self.cursor.execute("DELETE FROM english_vietnamese")
            
            self.cursor.execute("""
                INSERT INTO english_vietnamese (id, english_word, vietnamese_meaning, word_type, pronunciation, example)
                SELECT id, english_word, vietnamese_meaning, word_type, pronunciation, example
                FROM english_vietnamese_temp
            """)
            
            self.cursor.execute("DROP TABLE english_vietnamese_temp")
            
            # Xử lý trùng lặp Việt-Anh
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vietnamese_english_temp AS
                SELECT MIN(id) as id, vietnamese_word, english_meaning, word_type, example
                FROM vietnamese_english
                GROUP BY vietnamese_word, english_meaning
            """)
            
            self.cursor.execute("DELETE FROM vietnamese_english")
            
            self.cursor.execute("""
                INSERT INTO vietnamese_english (id, vietnamese_word, english_meaning, word_type, example)
                SELECT id, vietnamese_word, english_meaning, word_type, example
                FROM vietnamese_english_temp
            """)
            
            self.cursor.execute("DROP TABLE vietnamese_english_temp")
            
            self.conn.commit()
            print("Duplicate entries removed")
            
        except Exception as e:
            logging.error(f"Error removing duplicates: {e}")
            print(f"Error removing duplicates: {e}")
    
    def get_counts(self):
        """Lấy số lượng bản ghi cho mỗi bảng"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM english_vietnamese")
            en_vi_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM vietnamese_english")
            vi_en_count = self.cursor.fetchone()[0]
            
            return {
                'en_vi': en_vi_count,
                'vi_en': vi_en_count
            }
        except Exception as e:
            logging.error(f"Error getting counts: {e}")
            return {'en_vi': 0, 'vi_en': 0}
    
    def get_vietnamese_words(self, limit=5000):
        """Lấy danh sách các từ tiếng Việt từ cơ sở dữ liệu"""
        try:
            self.cursor.execute(f"SELECT DISTINCT vietnamese_word FROM vietnamese_english LIMIT {limit}")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting Vietnamese words: {e}")
            return []
    
    def get_translations(self, limit=50000):
        """Lấy các bản dịch hiện có từ cơ sở dữ liệu"""
        try:
            self.cursor.execute(f"SELECT DISTINCT english_word, vietnamese_meaning FROM english_vietnamese LIMIT {limit}")
            return {row[0].lower(): row[1] for row in self.cursor.fetchall()}
        except Exception as e:
            logging.error(f"Error getting translations: {e}")
            return {}
    
    def export_to_sql_file(self, output_file='dictionary_data.sql', batch_size=1000):
        """Xuất dữ liệu từ điển ra file SQL"""
        try:
            counts = self.get_counts()
            en_vi_count = counts['en_vi']
            vi_en_count = counts['vi_en']
            
            print(f"Exporting {en_vi_count} EN-VI and {vi_en_count} VI-EN entries to {output_file}...")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Ghi schema
                schema_sql = """
CREATE TABLE IF NOT EXISTS english_vietnamese (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    english_word VARCHAR(255) NOT NULL,
    vietnamese_meaning TEXT NOT NULL,
    word_type VARCHAR(50),
    pronunciation VARCHAR(255),
    example TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vietnamese_english (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vietnamese_word VARCHAR(255) NOT NULL,
    english_meaning TEXT NOT NULL,
    word_type VARCHAR(50),
    example TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_english_word ON english_vietnamese(english_word);
CREATE INDEX idx_vietnamese_word ON vietnamese_english(vietnamese_word);
                """
                f.write(schema_sql + "\n\n")
                
                # Ghi dữ liệu Anh-Việt theo lô
                f.write("-- English-Vietnamese data\n")
                
                for offset in tqdm(range(0, en_vi_count, batch_size), desc="Exporting EN-VI"):
                    self.cursor.execute(f"""
                        SELECT english_word, vietnamese_meaning, word_type, pronunciation, example 
                        FROM english_vietnamese
                        LIMIT {batch_size} OFFSET {offset}
                    """)
                    rows = self.cursor.fetchall()
                    
                    for row in rows:
                        english_word, vietnamese_meaning, word_type, pronunciation, example = row
                        # Escape các ký tự đặc biệt
                        english_word = str(english_word).replace("'", "''")
                        vietnamese_meaning = str(vietnamese_meaning).replace("'", "''")
                        word_type = str(word_type or "").replace("'", "''")
                        pronunciation = str(pronunciation or "").replace("'", "''")
                        example = str(example or "").replace("'", "''")
                        
                        f.write(f"INSERT INTO english_vietnamese (english_word, vietnamese_meaning, word_type, pronunciation, example) VALUES ('{english_word}', '{vietnamese_meaning}', '{word_type}', '{pronunciation}', '{example}');\n")
                
                # Ghi dữ liệu Việt-Anh theo lô
                f.write("\n-- Vietnamese-English data\n")
                
                for offset in tqdm(range(0, vi_en_count, batch_size), desc="Exporting VI-EN"):
                    self.cursor.execute(f"""
                        SELECT vietnamese_word, english_meaning, word_type, example 
                        FROM vietnamese_english
                        LIMIT {batch_size} OFFSET {offset}
                    """)
                    rows = self.cursor.fetchall()
                    
                    for row in rows:
                        vietnamese_word, english_meaning, word_type, example = row
                        # Escape các ký tự đặc biệt
                        vietnamese_word = str(vietnamese_word).replace("'", "''")
                        english_meaning = str(english_meaning).replace("'", "''")
                        word_type = str(word_type or "").replace("'", "''")
                        example = str(example or "").replace("'", "''")
                        
                        f.write(f"INSERT INTO vietnamese_english (vietnamese_word, english_meaning, word_type, example) VALUES ('{vietnamese_word}', '{english_meaning}', '{word_type}', '{example}');\n")
            
            print(f"Successfully exported data to {output_file}")
            return True
        except Exception as e:
            logging.error(f"Error exporting to SQL file: {e}")
            print(f"Error exporting to SQL file: {e}")
            return False
    
    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()