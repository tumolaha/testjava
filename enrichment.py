import logging
from config import COMMON_POS, COMMON_PRONUNCIATIONS, COMMON_EXAMPLES

def enrich_data(db):
    """Làm giàu dữ liệu từ điển với thông tin bổ sung"""
    print("Enriching dictionary data...")
    
    # Thêm thông tin loại từ nơi thiếu
    _enrich_part_of_speech(db)
    
    # Thêm phát âm nơi thiếu
    _enrich_pronunciations(db)
    
    # Thêm ví dụ nơi thiếu
    _enrich_examples(db)
    
    print("Data enrichment completed")

def _enrich_part_of_speech(db):
    """Thêm thông tin loại từ nơi thiếu"""
    print("Adding part of speech information...")
    
    try:
        # Cập nhật các mục Anh-Việt
        for word, pos in COMMON_POS.items():
            db.cursor.execute(
                "UPDATE english_vietnamese SET word_type = ? WHERE LOWER(english_word) = ? AND (word_type IS NULL OR word_type = '')",
                (pos, word.lower())
            )
        
        db.conn.commit()
        print("Updated part of speech for English-Vietnamese entries")
        
    except Exception as e:
        logging.error(f"Error enriching part of speech: {e}")

def _enrich_pronunciations(db):
    """Thêm phát âm nơi thiếu"""
    print("Adding pronunciations where missing...")
    
    try:
        # Cập nhật các mục Anh-Việt
        for word, pron in COMMON_PRONUNCIATIONS.items():
            db.cursor.execute(
                "UPDATE english_vietnamese SET pronunciation = ? WHERE LOWER(english_word) = ? AND (pronunciation IS NULL OR pronunciation = '')",
                (pron, word.lower())
            )
        
        db.conn.commit()
        print("Updated pronunciations for common words")
        
    except Exception as e:
        logging.error(f"Error enriching pronunciations: {e}")

def _enrich_examples(db):
    """Thêm ví dụ nơi thiếu"""
    print("Adding example sentences where missing...")
    
    try:
        # Cập nhật các mục Anh-Việt
        for word, example in COMMON_EXAMPLES.items():
            db.cursor.execute(
                "UPDATE english_vietnamese SET example = ? WHERE LOWER(english_word) = ? AND (example IS NULL OR example = '')",
                (example, word.lower())
            )
        
        db.conn.commit()
        print("Updated examples for common words")
        
    except Exception as e:
        logging.error(f"Error enriching examples: {e}")