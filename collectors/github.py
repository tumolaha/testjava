import os
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CACHE_DIR, GITHUB_SOURCES
from processors.text import process_en_vi_txt, process_vi_en_txt
from processors.csv import process_en_vi_csv, process_vi_en_csv

def download_and_process_source(source, db):
    """Tải và xử lý một nguồn từ GitHub"""
    cache_file = f"{CACHE_DIR}/{source['name']}.{source['format']}"
    
    try:
        # Tải nếu chưa lưu cache
        if not os.path.exists(cache_file):
            print(f"Downloading {source['name']}...")
            urllib.request.urlretrieve(source['url'], cache_file)
        
        # Xử lý dựa trên loại và định dạng
        if source['format'] == 'txt':
            if source['type'] == 'en-vi':
                entries = process_en_vi_txt(cache_file)
                if entries:
                    count = db.batch_insert_en_vi(entries)
                    return count
            elif source['type'] == 'vi-en':
                entries = process_vi_en_txt(cache_file)
                if entries:
                    count = db.batch_insert_vi_en(entries)
                    return count
        elif source['format'] == 'csv':
            if source['type'] == 'en-vi':
                entries = process_en_vi_csv(cache_file)
                if entries:
                    count = db.batch_insert_en_vi(entries)
                    return count
            elif source['type'] == 'vi-en':
                entries = process_vi_en_csv(cache_file)
                if entries:
                    count = db.batch_insert_vi_en(entries)
                    return count
        
        return 0
    except Exception as e:
        logging.error(f"Error processing {source['name']}: {e}")
        return 0

def download_github_dictionaries(db):
    """Tải từ điển từ các kho GitHub"""
    print("Downloading dictionaries from GitHub repositories...")
    
    total_entries = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {
            executor.submit(download_and_process_source, source, db): source 
            for source in GITHUB_SOURCES
        }
        
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                result = future.result()
                if result:
                    total_entries += result
                    print(f"Downloaded and processed {source['name']}: {result} entries")
                else:
                    print(f"Failed to download or process {source['name']}")
            except Exception as e:
                print(f"Error processing {source['name']}: {e}")
    
    return total_entries