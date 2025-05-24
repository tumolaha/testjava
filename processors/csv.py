import pandas as pd
import logging

def process_en_vi_csv(file_path):
    """Process English-Vietnamese CSV dictionary"""
    entries = []
    try:
        df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        
        # Determine column mapping
        en_col = next((col for col in df.columns if col.lower() in ['english', 'en', 'word', 'en_word', 'english_word']), df.columns[0])
        vi_col = next((col for col in df.columns if col.lower() in ['vietnamese', 'vi', 'meaning', 'vi_meaning', 'vietnamese_meaning']), df.columns[1])
        type_col = next((col for col in df.columns if col.lower() in ['type', 'word_type', 'pos', 'part_of_speech']), None)
        pron_col = next((col for col in df.columns if col.lower() in ['pronunciation', 'pron', 'ipa']), None)
        ex_col = next((col for col in df.columns if col.lower() in ['example', 'ex', 'sample']), None)
        
        for _, row in df.iterrows():
            try:
                english_word = str(row[en_col]).strip()
                vietnamese_meaning = str(row[vi_col]).strip()
                
                if not english_word or not vietnamese_meaning or pd.isna(english_word) or pd.isna(vietnamese_meaning):
                    continue
                
                word_type = str(row[type_col]).strip() if type_col and not pd.isna(row[type_col]) else ""
                pronunciation = str(row[pron_col]).strip() if pron_col and not pd.isna(row[pron_col]) else ""
                example = str(row[ex_col]).strip() if ex_col and not pd.isna(row[ex_col]) else ""
                
                entries.append({
                    "english_word": english_word,
                    "vietnamese_meaning": vietnamese_meaning,
                    "word_type": word_type,
                    "pronunciation": pronunciation,
                    "example": example
                })
            except Exception as e:
                logging.error(f"Error processing row in {file_path}: {e}")
        
        return entries
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
        return []

def process_vi_en_csv(file_path):
    """Process Vietnamese-English CSV dictionary"""
    entries = []
    try:
        df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        
        # Determine column mapping
        vi_col = next((col for col in df.columns if col.lower() in ['vietnamese', 'vi', 'word', 'vi_word', 'vietnamese_word']), df.columns[0])
        en_col = next((col for col in df.columns if col.lower() in ['english', 'en', 'meaning', 'en_meaning', 'english_meaning']), df.columns[1])
        type_col = next((col for col in df.columns if col.lower() in ['type', 'word_type', 'pos', 'part_of_speech']), None)
        ex_col = next((col for col in df.columns if col.lower() in ['example', 'ex', 'sample']), None)
        
        for _, row in df.iterrows():
            try:
                vietnamese_word = str(row[vi_col]).strip()
                english_meaning = str(row[en_col]).strip()
                
                if not vietnamese_word or not english_meaning or pd.isna(vietnamese_word) or pd.isna(english_meaning):
                    continue
                
                word_type = str(row[type_col]).strip() if type_col and not pd.isna(row[type_col]) else ""
                example = str(row[ex_col]).strip() if ex_col and not pd.isna(row[ex_col]) else ""
                
                entries.append({
                    "vietnamese_word": vietnamese_word,
                    "english_meaning": english_meaning,
                    "word_type": word_type,
                    "example": example
                })
            except Exception as e:
                logging.error(f"Error processing row in {file_path}: {e}")
        
        return entries
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
        return []