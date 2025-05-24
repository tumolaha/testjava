import os
import time
import random
import logging
import urllib.request
import requests
from tqdm import tqdm

# Danh sách User-Agent để tránh bị phát hiện khi crawl
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
]

def get_random_user_agent():
    """Trả về một User-Agent ngẫu nhiên để tránh bị phát hiện khi crawl"""
    return random.choice(USER_AGENTS)

def create_directory(directory_path):
    """Tạo thư mục nếu chưa tồn tại"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Created directory: {directory_path}")
    return directory_path

def download_file(url, save_path, use_cache=True):
    """
    Tải tệp từ URL và lưu vào đường dẫn được chỉ định.
    Trả về True nếu tải xuống thành công, False nếu thất bại.
    """
    # Kiểm tra cache nếu được yêu cầu
    if use_cache and os.path.exists(save_path):
        logging.info(f"Using cached file: {save_path}")
        return True
    
    try:
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Tải tệp với User-Agent ngẫu nhiên
        headers = {'User-Agent': get_random_user_agent()}
        logging.info(f"Downloading file from {url} to {save_path}")
        
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            
            # Lấy kích thước tệp nếu có
            total_size = int(response.headers.get('content-length', 0))
            
            # Tải xuống với thanh tiến trình
            with open(save_path, 'wb') as file, tqdm(
                desc=os.path.basename(save_path),
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = file.write(chunk)
                    bar.update(size)
        
        logging.info(f"Successfully downloaded file to {save_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error downloading file from {url}: {e}")
        # Xóa tệp không hoàn chỉnh nếu có
        if os.path.exists(save_path):
            os.remove(save_path)
        return False

def download_file_simple(url, save_path, use_cache=True):
    """
    Phiên bản đơn giản hơn của hàm download_file sử dụng urllib
    """
    if use_cache and os.path.exists(save_path):
        logging.info(f"Using cached file: {save_path}")
        return True
    
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urllib.request.urlretrieve(url, save_path)
        logging.info(f"Successfully downloaded file to {save_path}")
        return True
    except Exception as e:
        logging.error(f"Error downloading file from {url}: {e}")
        return False

def clean_text(text):
    """Làm sạch văn bản, loại bỏ ký tự đặc biệt"""
    if not text:
        return ""
    
    # Loại bỏ khoảng trắng thừa
    text = text.strip()
    
    # Thay thế nhiều khoảng trắng bằng một khoảng trắng
    text = ' '.join(text.split())
    
    return text

def escape_sql(text):
    """Escape các ký tự đặc biệt cho SQL"""
    if not text:
        return ""
    return str(text).replace("'", "''")

def normalize_word(word):
    """Chuẩn hóa từ cho việc so sánh"""
    if not word:
        return ""
    
    # Chuyển về chữ thường và loại bỏ khoảng trắng thừa
    word = word.lower().strip()
    
    return word

def format_time(seconds):
    """Định dạng thời gian từ giây thành hh:mm:ss"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    if h > 0:
        return f"{int(h)}h {int(m)}m {int(s)}s"
    elif m > 0:
        return f"{int(m)}m {int(s)}s"
    else:
        return f"{s:.1f}s"

def timer(func):
    """Decorator để đo thời gian thực thi của một hàm"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logging.info(f"{func.__name__} completed in {format_time(elapsed_time)}")
        return result
    return wrapper

def is_valid_word_entry(entry, type="en_vi"):
    """Kiểm tra xem mục từ điển có hợp lệ không"""
    if type == "en_vi":
        # Kiểm tra mục Anh-Việt
        return (
            entry.get("english_word") and 
            entry.get("vietnamese_meaning") and
            isinstance(entry.get("english_word"), str) and
            isinstance(entry.get("vietnamese_meaning"), str)
        )
    else:
        # Kiểm tra mục Việt-Anh
        return (
            entry.get("vietnamese_word") and 
            entry.get("english_meaning") and
            isinstance(entry.get("vietnamese_word"), str) and
            isinstance(entry.get("english_meaning"), str)
        )

def batch_process(items, process_func, batch_size=1000, desc="Processing"):
    """Xử lý các mục theo lô và hiển thị thanh tiến trình"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_results = process_func(batch)
        results.extend(batch_results)
        
    return results

def print_summary(title, items_count, elapsed_time):
    """In tóm tắt thực thi"""
    print(f"\n=== {title} ===")
    for key, value in items_count.items():
        print(f"- {key}: {value:,}")
    print(f"- Thời gian thực thi: {format_time(elapsed_time)}")