import logging
from tqdm import tqdm

def process_parallel_corpus(en_file, vi_file, max_entries=100000):
    """Process parallel corpus files to extract dictionary entries"""
    en_vi_entries = []
    vi_en_entries = []
    
    try:
        with open(en_file, 'r', encoding='utf-8', errors='ignore') as en_f, \
             open(vi_file, 'r', encoding='utf-8', errors='ignore') as vi_f:
            
            en_lines = en_f.readlines()
            vi_lines = vi_f.readlines()
            
            # Process only up to the max number of entries to avoid memory issues
            for i in tqdm(range(min(len(en_lines), len(vi_lines), max_entries)), desc="Processing parallel corpus"):
                en_line = en_lines[i].strip()
                vi_line = vi_lines[i].strip()
                
                en_word_count = len(en_line.split())
                vi_word_count = len(vi_line.split())
                
                # Only consider short phrases (1-3 words) that are likely to be dictionary entries
                if 1 <= en_word_count <= 3 and 1 <= vi_word_count <= 3:
                    # Add to English-Vietnamese
                    en_vi_entries.append({
                        "english_word": en_line,
                        "vietnamese_meaning": vi_line,
                        "word_type": "",
                        "pronunciation": "",
                        "example": ""
                    })
                    
                    # Add to Vietnamese-English
                    vi_en_entries.append({
                        "vietnamese_word": vi_line,
                        "english_meaning": en_line,
                        "word_type": "",
                        "example": ""
                    })
        
        return {
            "en_vi": en_vi_entries,
            "vi_en": vi_en_entries
        }
    
    except Exception as e:
        logging.error(f"Error processing parallel corpus: {e}")
        return {
            "en_vi": [],
            "vi_en": []
        }