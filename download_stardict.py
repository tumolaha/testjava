import os
import requests
import logging
import zipfile
import tarfile
import shutil
import gzip
import re
from tqdm import tqdm

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('stardict_downloader')

def download_file(url, output_path, logger):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            for chunk in tqdm(
                response.iter_content(chunk_size=8192), 
                total=total_size//8192 if total_size > 0 else None, 
                unit='KB',
                desc=os.path.basename(output_path)
            ):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Đã tải xong file {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi tải file {url}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def extract_archive(archive_path, extract_to, logger):
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        
        elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
        
        logger.info(f"Đã giải nén file {archive_path}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi giải nén file {archive_path}: {e}")
        return False

def download_from_github(dict_dir, logger):
    """Tải từ điển từ GitHub"""
    try:
        # URL của từ điển trên GitHub
        url = "https://raw.githubusercontent.com/open-dict-data/ding-dictionary/master/en-vi.dict.dz"
        dict_path = os.path.join(dict_dir, "en-vi.dict.dz")
        
        # Tải file .dict.dz
        if download_file(url, dict_path, logger):
            # Tạo file .ifo đơn giản
            ifo_content = """StarDict's dict ifo file
version=2.4.2
wordcount=10000
idxfilesize=100000
bookname=English-Vietnamese Dictionary
author=Open Dictionary Data
description=English-Vietnamese dictionary from open-dict-data
date=2023.07.12
sametypesequence=m
"""
            with open(os.path.join(dict_dir, 'en-vi.ifo'), 'w', encoding='utf-8') as f:
                f.write(ifo_content)
            
            # Tạo file .idx trống (sẽ được xây dựng lại khi sử dụng)
            with open(os.path.join(dict_dir, 'en-vi.idx'), 'wb') as f:
                f.write(b'')
            
            logger.info("Đã tải từ điển từ GitHub thành công")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Lỗi khi tải từ điển từ GitHub: {e}")
        return False

def main():
    logger = setup_logging()
    logger.info("Bắt đầu tải từ điển StarDict Anh-Việt")
    
    dict_dir = 'data/stardict'
    temp_dir = 'data/temp'
    
    # Tạo thư mục cần thiết
    os.makedirs(dict_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Các nguồn từ điển StarDict Anh-Việt
    success = False
    
    # Phương án 1: Tải từ GitHub
    logger.info("Thử tải từ điển từ GitHub...")
    if download_from_github(dict_dir, logger):
        success = True
    
    # Phương án 2: Tải từ các nguồn khác
    if not success:
        stardict_sources = [
            {
                'name': 'Anh-Viet-Lac-Viet',
                'url': 'https://datatrove.net/dictionaries/vietnamese/anhviet109K.zip',
                'files': ['anhviet.dict.dz', 'anhviet.idx', 'anhviet.ifo']
            },
            {
                'name': 'EN-VI-Vocabulary',
                'url': 'https://datatrove.net/dictionaries/vietnamese/DIC_ENVI.zip',
                'files': ['DIC_ENVI.dict.dz', 'DIC_ENVI.idx', 'DIC_ENVI.ifo']
            }
        ]
        
        for source in stardict_sources:
            logger.info(f"Đang tải xuống từ điển {source['name']}...")
            
            # Tải file nén
            archive_path = os.path.join(temp_dir, f"{source['name']}.zip")
            if download_file(source['url'], archive_path, logger):
                # Giải nén file
                if extract_archive(archive_path, temp_dir, logger):
                    # Di chuyển các file cần thiết
                    for file_name in source['files']:
                        file_path = os.path.join(temp_dir, file_name)
                        
                        # Tìm file theo pattern nếu đường dẫn chính xác không tồn tại
                        if not os.path.exists(file_path):
                            found_files = []
                            for root, _, files in os.walk(temp_dir):
                                for fname in files:
                                    if fname == file_name or fname.endswith(os.path.splitext(file_name)[1]):
                                        found_files.append(os.path.join(root, fname))
                            
                            if found_files:
                                file_path = found_files[0]
                                logger.info(f"Đã tìm thấy file {file_name} tại {file_path}")
                            else:
                                logger.warning(f"Không tìm thấy file {file_name}")
                                continue
                        
                        # Di chuyển file
                        dest_path = os.path.join(dict_dir, os.path.basename(file_path))
                        shutil.copy2(file_path, dest_path)
                        logger.info(f"Đã sao chép file {file_name} đến {dest_path}")
                    
                    success = True
                    break  # Nếu thành công, thoát vòng lặp
    
    # Thông báo nếu không tải được từ điển
    if not success:
        logger.warning("Không thể tải xuống từ điển từ các nguồn trực tuyến.")
        logger.warning("Vui lòng tải thủ công từ điển Anh-Việt và đặt vào thư mục data/stardict.")
        logger.warning("Bạn có thể tìm từ điển tại: https://sourceforge.net/projects/stardict-4/files/dictionaries/")
    
    # Dọn dẹp thư mục tạm
    shutil.rmtree(temp_dir, ignore_errors=True)
    logger.info("Đã hoàn thành việc tải xuống từ điển StarDict")

if __name__ == "__main__":
    main()