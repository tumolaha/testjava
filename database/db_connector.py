import psycopg2
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'dictionary_db'),
            'user': os.getenv('DB_USER', 'dict_admin'),
            'password': os.getenv('DB_PASS', '')
        }
        
        self.logger = logging.getLogger('db_connector')
    
    def connect(self):
        """Kết nối đến cơ sở dữ liệu PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            
            # Test the connection by trying to execute a simple query
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            
            if result and result[0] == 1:
                self.logger.info("Kết nối thành công đến PostgreSQL")
                
                # Check permissions on the tables
                try:
                    self.cursor.execute("SELECT * FROM words LIMIT 0")
                    self.logger.info("Có quyền truy cập bảng words")
                except Exception as e:
                    self.logger.error(f"Không có quyền truy cập bảng words: {e}")
                    self.logger.info("Vui lòng chạy script fix_permissions.sh để khắc phục")
                    return False
                    
                return True
            else:
                self.logger.error("Không thể kết nối đến PostgreSQL")
                return False
                
        except Exception as e:
            self.logger.error(f"Lỗi kết nối PostgreSQL: {e}")
            
            # Provide more helpful error messages based on common issues
            if "password authentication failed" in str(e).lower():
                self.logger.error("Sai mật khẩu. Vui lòng kiểm tra thông tin đăng nhập trong file .env")
            elif "database" in str(e).lower() and "does not exist" in str(e).lower():
                self.logger.error("Cơ sở dữ liệu không tồn tại. Vui lòng chạy script setup_database.sh")
                
            return False
    
    def disconnect(self):
        """Đóng kết nối đến cơ sở dữ liệu"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.logger.info("Đã đóng kết nối PostgreSQL")
    
    def execute_query(self, query, params=None, fetch=False):
        """Thực thi truy vấn SQL với tham số tùy chọn"""
        try:
            self.cursor.execute(query, params or ())
            if fetch:
                return self.cursor.fetchall()
            else:
                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Lỗi thực thi truy vấn: {e}")
            self.logger.error(f"Query: {query}, Params: {params}")
            return False
    
    def execute_and_fetchone(self, query, params=None):
        """Thực thi truy vấn và trả về một hàng kết quả"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Lỗi thực thi truy vấn: {e}")
            return None
    
    def insert_word(self, word, pronunciation):
        """Chèn từ mới vào bảng words và trả về ID"""
        query = "INSERT INTO words (word, pronunciation) VALUES (%s, %s) RETURNING id"
        result = self.execute_and_fetchone(query, (word, pronunciation))
        if result:
            return result[0]
        return None
    
    def word_exists(self, word):
        """Kiểm tra từ đã tồn tại trong cơ sở dữ liệu chưa"""
        query = "SELECT id FROM words WHERE word = %s"
        result = self.execute_and_fetchone(query, (word,))
        if result:
            return result[0]
        return None
    
    def export_to_sql(self, output_file):
        """Xuất cơ sở dữ liệu thành file SQL"""
        try:
            # Sử dụng pg_dump để xuất dữ liệu
            cmd = f"pg_dump -h {self.db_config['host']} -U {self.db_config['user']} -d {self.db_config['database']} -f {output_file}"
            os.environ['PGPASSWORD'] = self.db_config['password']
            result = os.system(cmd)
            if result == 0:
                self.logger.info(f"Đã xuất cơ sở dữ liệu sang {output_file}")
                return True
            else:
                self.logger.error(f"Lỗi xuất cơ sở dữ liệu, mã lỗi: {result}")
                return False
        except Exception as e:
            self.logger.error(f"Lỗi xuất SQL: {e}")
            return False

    def apply_improved_schema(self):
        """Áp dụng cấu trúc cơ sở dữ liệu cải tiến"""
        try:
            # Đọc file schema cải tiến
            schema_path = 'dictionary_schema_improved.sql'
            if not os.path.exists(schema_path):
                self.logger.error(f"Không tìm thấy file schema: {schema_path}")
                return False
                
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
                
            # Chia script thành các câu lệnh riêng biệt
            statements = schema.split(';')
            
            # Bắt đầu transaction
            self.conn.autocommit = False
            
            # Thực thi từng câu lệnh
            for statement in statements:
                statement = statement.strip()
                if statement:
                    # Bỏ qua các câu lệnh DROP TABLE nếu có
                    if not statement.lower().startswith('drop table'):
                        self.cursor.execute(statement)
            
            # Commit transaction
            self.conn.commit()
            self.conn.autocommit = True
            
            self.logger.info("Đã áp dụng cấu trúc cơ sở dữ liệu cải tiến")
            return True
            
        except Exception as e:
            self.logger.error(f"Lỗi khi áp dụng schema cải tiến: {e}")
            try:
                self.conn.rollback()
                self.conn.autocommit = True
            except:
                pass
            return False

    def get_dictionary_sources(self):
        """Lấy danh sách các nguồn từ điển"""
        try:
            # Kiểm tra xem bảng dictionary_sources có tồn tại không
            self.cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'dictionary_sources'
            )
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                return []
                
            self.cursor.execute("""
            SELECT id, name, description, url, enabled, priority 
            FROM dictionary_sources 
            ORDER BY priority DESC
            """)
            
            return self.cursor.fetchall()
            
        except Exception as e:
            self.logger.error(f"Lỗi khi lấy danh sách nguồn từ điển: {e}")
            return []