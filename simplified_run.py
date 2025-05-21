import logging
import nltk
import os
from datetime import datetime

def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = f"{log_dir}/simplified_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('simplified')

def main():
    logger = setup_logging()
    logger.info("Bắt đầu chạy chế độ đơn giản")
    
    # Tải dữ liệu WordNet
    try:
        logger.info("Tải dữ liệu WordNet...")
        nltk.download('wordnet')
        from nltk.corpus import wordnet as wn
    except Exception as e:
        logger.error(f"Lỗi khi tải WordNet: {e}")
        return
    
    # Danh sách từ để kiểm tra
    test_words = ["example", "computer", "language", "dictionary"]
    
    for word in test_words:
        logger.info(f"Đang tìm kiếm '{word}' trong WordNet")
        synsets = wn.synsets(word)
        
        if not synsets:
            logger.warning(f"Không tìm thấy '{word}' trong WordNet")
            continue
        
        logger.info(f"Tìm thấy {len(synsets)} đồng nghĩa (synsets) cho '{word}'")
        
        for i, synset in enumerate(synsets[:3], 1):  # Hiển thị tối đa 3 synsets
            pos = synset.pos()
            definition = synset.definition()
            examples = synset.examples()
            
            logger.info(f"  {i}. Loại từ: {pos}")
            logger.info(f"     Định nghĩa: {definition}")
            
            if examples:
                logger.info(f"     Ví dụ: {examples[0]}")
    
    logger.info("Hoàn thành chế độ đơn giản")

if __name__ == "__main__":
    main()