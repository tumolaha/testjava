import os
import zipfile
import tempfile
import logging
import urllib.request
import time
from tqdm import tqdm
from config import CACHE_DIR, OPUS_SOURCES

def download_opus_data(db):
    """Download and process OPUS parallel corpus data"""
    print("Downloading OPUS parallel corpus data...")
    
    total_entries = 0
    
    for source in OPUS_SOURCES:
        try:
            print(f"Processing {source['name']}...")
            
            cache_file = f"{CACHE_DIR}/{source['name']}.zip"
            
            # Download if not cached
            if not os.path.exists(cache_file):
                print(f"Downloading {source['name']}...")
                urllib.request.urlretrieve(source['url'], cache_file)
            
            # Extract and process files
            with zipfile.ZipFile(cache_file, 'r') as zip_ref:
                # Find the correct files in the archive
                en_file = None
                vi_file = None
                
                for file in zip_ref.namelist():
                    if file.endswith('.en'):
                        en_file = file
                    elif file.endswith('.vi'):
                        vi_file = file
                
                if en_file and vi_file:
                    # Extract both files to temporary directory
                    temp_dir = tempfile.mkdtemp()
                    zip_ref.extract(en_file, temp_dir)
                    zip_ref.extract(vi_file, temp_dir)
                    
                    # Process the files
                    entries = _process_parallel_corpus(
                        os.path.join(temp_dir, en_file),
                        os.path.join(temp_dir, vi_file),
                        source['alignment']
                    )
                    
                    # Clean up
                    import shutil
                    shutil.rmtree(temp_dir)
                    
                    # Add entries to database
                    if entries['en_vi']:
                        count_en_vi = db.batch_insert_en_vi(entries['en_vi'])
                    else:
                        count_en_vi = 0
                        
                    if entries['vi_en']:
                        count_vi_en = db.batch_insert_vi_en(entries['vi_en'])
                    else:
                        count_vi_en = 0
                    
                    total_entries += count_en_vi + count_vi_en
                    print(f"Processed {count_en_vi} EN-VI and {count_vi_en} VI-EN entries from {source['name']}")
                else:
                    print(f"Could not find required files in {source['name']} archive")
        
        except Exception as e:
            logging.error(f"Error processing {source['name']}: {e}")
    
    return total_entries

def _process_parallel_corpus(source_file, target_file, alignment):
    """Process parallel corpus files to extract dictionary entries"""
    en_vi_entries = []
    vi_en_entries = []
    
    try:
        with open(source_file, 'r', encoding='utf-8', errors='ignore') as src_f, \
             open(target_file, 'r', encoding='utf-8', errors='ignore') as tgt_f:
            
            src_lines = src_f.readlines()
            tgt_lines = tgt_f.readlines()
            
            # Keep only lines with 1-3 words (likely single terms)
            dictionary_pairs = []
            
            for i in tqdm(range(min(len(src_lines), len(tgt_lines))), desc="Processing corpus pairs"):
                src_line = src_lines[i].strip()
                tgt_line = tgt_lines[i].strip()
                
                src_word_count = len(src_line.split())
                tgt_word_count = len(tgt_line.split())
                
                # Only consider short phrases that are likely to be dictionary entries
                if 1 <= src_word_count <= 3 and 1 <= tgt_word_count <= 3:
                    dictionary_pairs.append((src_line, tgt_line))
            
            # Process pairs based on alignment direction
            if alignment == 'en-vi':
                for en, vi in dictionary_pairs:
                    # Add to English-Vietnamese
                    en_vi_entries.append({
                        "english_word": en,
                        "vietnamese_meaning": vi,
                        "word_type": "",
                        "pronunciation": "",
                        "example": ""
                    })
                    
                    # Add to Vietnamese-English
                    vi_en_entries.append({
                        "vietnamese_word": vi,
                        "english_meaning": en,
                        "word_type": "",
                        "example": ""
                    })
            else:  # vi-en
                for vi, en in dictionary_pairs:
                    # Add to Vietnamese-English
                    vi_en_entries.append({
                        "vietnamese_word": vi,
                        "english_meaning": en,
                        "word_type": "",
                        "example": ""
                    })
                    
                    # Add to English-Vietnamese
                    en_vi_entries.append({
                        "english_word": en,
                        "vietnamese_meaning": vi,
                        "word_type": "",
                        "pronunciation": "",
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