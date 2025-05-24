import logging

def process_en_vi_txt(file_path):
    """Xử lý file văn bản từ điển Anh-Việt"""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        english_word = parts[0].strip()
                        vietnamese_meaning = parts[1].strip()
                        
                        # Trích xuất các trường bổ sung nếu có
                        word_type = parts[2].strip() if len(parts) > 2 else ""
                        pronunciation = parts[3].strip() if len(parts) > 3 else ""
                        example = parts[4].strip() if len(parts) > 4 else ""
                        
                        entries.append({
                            "english_word": english_word,
                            "vietnamese_meaning": vietnamese_meaning,
                            "word_type": word_type,
                            "pronunciation": pronunciation,
                            "example": example
                        })
                except Exception as e:
                    logging.error(f"Error processing line in {file_path}: {e}")
        
        return entries
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []

def process_vi_en_txt(file_path):
    """Xử lý file văn bản từ điển Việt-Anh"""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        vietnamese_word = parts[0].strip()
                        english_meaning = parts[1].strip()
                        
                        # Trích xuất các trường bổ sung nếu có
                        word_type = parts[2].strip() if len(parts) > 2 else ""
                        example = parts[3].strip() if len(parts) > 3 else ""
                        
                        entries.append({
                            "vietnamese_word": vietnamese_word,
                            "english_meaning": english_meaning,
                            "word_type": word_type,
                            "example": example
                        })
                except Exception as e:
                    logging.error(f"Error processing line in {file_path}: {e}")
        
        return entries
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []