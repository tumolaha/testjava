import os
import logging
import sqlite3
from scrapers.stardict_anh_viet import StarDictAnhViet

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('dict_checker')

def check_stardict_files():
    """Kiểm tra các file từ điển StarDict"""
    logger = setup_logging()
    
    dict_dir = 'data/stardict'
    if not os.path.exists(dict_dir):
        logger.error(f"Thư mục từ điển không tồn tại: {dict_dir}")
        return False
    
    # Tìm tất cả các file từ điển
    dict_files = []
    for file in os.listdir(dict_dir):
        if file.endswith('.dict.dz') or file.endswith('.dict'):
            dict_path = os.path.join(dict_dir, file)
            ifo_path = os.path.join(dict_dir, file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo'))
            
            dict_files.append({
                'dict': dict_path,
                'ifo': ifo_path if os.path.exists(ifo_path) else None,
                'name': os.path.basename(file).split('.')[0]
            })
    
    if not dict_files:
        logger.warning("Không tìm thấy file từ điển nào trong thư mục data/stardict")
        return False
    
    logger.info(f"Tìm thấy {len(dict_files)} file từ điển:")
    for i, d in enumerate(dict_files, 1):
        logger.info(f"{i}. {d['name']} - {d['dict']}")
    
    # Kiểm tra và nhập từ điển
    stardict = StarDictAnhViet()
    
    success = False
    for d in dict_files:
        logger.info(f"Đang kiểm tra từ điển {d['name']}...")
        if stardict.import_dict_file(d['dict'], d['ifo'], d['name']):
            success = True
    
    # Kiểm tra số lượng từ
    try:
        conn = sqlite3.connect(stardict.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dictionary")
        count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(DISTINCT word) FROM dictionary")
        unique_count = c.fetchone()[0]
        
        c.execute("SELECT source, COUNT(*) FROM dictionary GROUP BY source")
        sources = c.fetchall()
        
        conn.close()
        
        logger.info(f"Tổng số từ: {count}")
        logger.info(f"Số từ duy nhất: {unique_count}")
        logger.info("Số từ theo nguồn:")
        for source, src_count in sources:
            logger.info(f"  - {source}: {src_count}")
        
        # Thử tìm một số từ cơ bản
        test_words = ["book", "hello", "computer", "example", "dictionary"]
        logger.info("Thử tìm các từ cơ bản:")
        
        for word in test_words:
            word_data = stardict.get_word_data(word)
            if word_data:
                defs = [d.get('definition_vi', '') for d in word_data.get('definitions', [])]
                logger.info(f"  - {word}: {len(defs)} định nghĩa, đầu tiên: {defs[0] if defs else 'Không có'}")
            else:
                logger.info(f"  - {word}: Không tìm thấy")
        
        return success and count > 0
        
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra từ điển: {e}")
        return False

if __name__ == "__main__":
    if check_stardict_files():
        print("Từ điển hoạt động tốt!")
    else:
        print("Có vấn đề với từ điển. Vui lòng kiểm tra log để biết thêm chi tiết.")