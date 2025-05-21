import os
import logging
import sqlite3
import glob
from scrapers.stardict_anh_viet import StarDictAnhViet

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('dict_checker')

def find_dictionaries():
    """Tìm tất cả các file từ điển trong thư mục dữ liệu"""
    logger = setup_logging()
    
    dict_dirs = ['data/dictionaries', 'data/stardict']
    dict_files = []
    
    for dict_dir in dict_dirs:
        if not os.path.exists(dict_dir):
            continue
            
        logger.info(f"Kiểm tra thư mục {dict_dir}...")
        
        # Tìm tất cả các file .dict và .dict.dz
        for dict_file in glob.glob(f"{dict_dir}/*.dict*"):
            name = os.path.basename(dict_file).split('.')[0]
            ifo_file = dict_file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo')
            
            dict_files.append({
                'name': name,
                'dict': dict_file,
                'ifo': ifo_file if os.path.exists(ifo_file) else None,
                'dir': dict_dir
            })
            
        # Tìm file văn bản đơn giản
        for text_file in glob.glob(f"{dict_dir}/*.txt"):
            if os.path.basename(text_file) != 'report.txt':
                dict_files.append({
                    'name': os.path.basename(text_file).split('.')[0],
                    'dict': text_file,
                    'ifo': None,
                    'dir': dict_dir,
                    'type': 'text'
                })
    
    logger.info(f"Tìm thấy {len(dict_files)} file từ điển")
    return dict_files

def check_dictionaries():
    """Kiểm tra tất cả các từ điển đã tìm thấy"""
    logger = setup_logging()
    
    # Tìm các file từ điển
    dict_files = find_dictionaries()
    
    if not dict_files:
        logger.warning("Không tìm thấy file từ điển nào")
        return False
    
    # In danh sách từ điển
    logger.info("\n=== DANH SÁCH TỪ ĐIỂN ĐÃ TÌM THẤY ===")
    for i, d in enumerate(dict_files, 1):
        logger.info(f"{i}. {d['name']} - {d['dict']}")
    
    # Khởi tạo StarDict
    stardict = StarDictAnhViet(db_path='data/tmp_dictionary_check.db')
    
    # Nếu có file cũ, xóa đi để kiểm tra lại từ đầu
    if os.path.exists(stardict.db_path):
        os.remove(stardict.db_path)
    
    # Nhập từng từ điển
    for d in dict_files:
        logger.info(f"\n--- Kiểm tra từ điển: {d['name']} ---")
        
        if d.get('type') == 'text':
            # Nhập từ điển văn bản
            if stardict.import_text_dictionary(d['dict'], d['name']):
                logger.info(f"Đã nhập thành công từ điển văn bản {d['name']}")
            else:
                logger.warning(f"Không thể nhập từ điển văn bản {d['name']}")
        else:
            # Nhập từ điển StarDict
            if stardict.import_dict_file(d['dict'], d['ifo'], d['name']):
                logger.info(f"Đã nhập thành công từ điển {d['name']}")
            else:
                logger.warning(f"Không thể nhập từ điển {d['name']}")
    
    # Kiểm tra số lượng từ
    try:
        conn = sqlite3.connect(stardict.db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM dictionary")
        total_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(DISTINCT word) FROM dictionary")
        unique_words = c.fetchone()[0]
        
        c.execute("SELECT source, COUNT(*) FROM dictionary GROUP BY source")
        sources = c.fetchall()
        
        conn.close()
        
        logger.info("\n=== THỐNG KÊ TỪ ĐIỂN ===")
        logger.info(f"Tổng số từ: {total_count}")
        logger.info(f"Số từ duy nhất: {unique_words}")
        
        logger.info("\n=== THỐNG KÊ THEO NGUỒN ===")
        for source, count in sources:
            logger.info(f"{source}: {count} từ")
        
        # Kiểm tra một số từ phổ biến
        test_words = [
            "hello", "world", "computer", "book", "dictionary", "example", 
            "language", "love", "time", "day", "night", "house", "family"
        ]
        
        logger.info("\n=== KIỂM TRA TỪ PHỔ BIẾN ===")
        found_count = 0
        
        for word in test_words:
            data = stardict.get_word_data(word)
            if data:
                found_count += 1
                defs = [d.get('definition_vi', '') for d in data.get('definitions', [])]
                logger.info(f"{word}: {len(defs)} định nghĩa, đầu tiên: {defs[0][:100] if defs else 'Không có'}")
            else:
                logger.info(f"{word}: Không tìm thấy")
        
        logger.info(f"\nTìm thấy {found_count}/{len(test_words)} từ phổ biến")
        
        # Tạo báo cáo
        report_path = 'data/dictionaries/report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("BÁO CÁO KIỂM TRA TỪ ĐIỂN\n")
            f.write("=======================\n\n")
            
            f.write(f"Tổng số từ điển: {len(dict_files)}\n")
            f.write(f"Tổng số từ: {total_count}\n")
            f.write(f"Số từ duy nhất: {unique_words}\n\n")
            
            f.write("Thống kê theo nguồn:\n")
            for source, count in sources:
                f.write(f"- {source}: {count} từ\n")
            
            f.write("\nKết quả kiểm tra từ phổ biến:\n")
            f.write(f"- Tìm thấy {found_count}/{len(test_words)} từ\n")
            
        logger.info(f"\nĐã tạo báo cáo tại: {report_path}")
        
        return total_count > 0
        
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra từ điển: {e}")
        return False

def main():
    """Hàm chính"""
    logger = setup_logging()
    
    logger.info("Bắt đầu kiểm tra từ điển...")
    
    if check_dictionaries():
        logger.info("Kiểm tra từ điển thành công!")
        return 0
    else:
        logger.error("Kiểm tra từ điển thất bại!")
        return 1

if __name__ == "__main__":
    exit(main())