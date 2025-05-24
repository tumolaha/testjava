import os
import tarfile
import logging
import urllib.request
from tqdm import tqdm
from config import CACHE_DIR

def download_wordnet_data(db):
    """Download and process WordNet data with Vietnamese translations"""
    print("Downloading WordNet data...")
    
    # Create directory for WordNet data
    wordnet_dir = f"{CACHE_DIR}/wordnet"
    os.makedirs(wordnet_dir, exist_ok=True)
    
    try:
        # Get Vietnamese WordNet mapping
        vi_wordnet_file = f"{CACHE_DIR}/vietnamese-wordnet.txt"
        vi_wordnet_url = "https://raw.githubusercontent.com/vunb/vntk/master/data/resources/dictionaries/vi-en/wordnet_synset.txt"
        
        if not os.path.exists(vi_wordnet_file):
            print("Downloading Vietnamese WordNet mapping...")
            urllib.request.urlretrieve(vi_wordnet_url, vi_wordnet_file)
        
        # Create entries from the wordnet file
        entries_en_vi = []
        entries_vi_en = []
        
        with open(vi_wordnet_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in tqdm(f, desc="Processing WordNet entries"):
                try:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        synset_id = parts[0].strip()
                        vietnamese_words = parts[1].strip().split(',')
                        
                        # Extract part of speech from synset ID
                        pos = ""
                        if synset_id.startswith('n'):
                            pos = "noun"
                        elif synset_id.startswith('v'):
                            pos = "verb"
                        elif synset_id.startswith('a') or synset_id.startswith('s'):
                            pos = "adjective"
                        elif synset_id.startswith('r'):
                            pos = "adverb"
                        
                        # Use synset ID for English word (simplified approach)
                        # In a more complex implementation, we'd map synset IDs to actual English words
                        english_word = f"wordnet-{synset_id}"
                        
                        for vi_word in vietnamese_words:
                            vi_word = vi_word.strip()
                            if vi_word:
                                # Add to English-Vietnamese
                                entries_en_vi.append({
                                    "english_word": english_word,
                                    "vietnamese_meaning": vi_word,
                                    "word_type": pos,
                                    "pronunciation": "",
                                    "example": f"WordNet synset: {synset_id}"
                                })
                                
                                # Add to Vietnamese-English
                                entries_vi_en.append({
                                    "vietnamese_word": vi_word,
                                    "english_meaning": english_word,
                                    "word_type": pos,
                                    "example": f"WordNet synset: {synset_id}"
                                })
                except Exception as e:
                    logging.error(f"Error processing WordNet line: {e}")
        
        # Insert entries into database
        count_en_vi = db.batch_insert_en_vi(entries_en_vi)
        count_vi_en = db.batch_insert_vi_en(entries_vi_en)
        
        total_entries = count_en_vi + count_vi_en
        print(f"Processed {count_en_vi} EN-VI and {count_vi_en} VI-EN entries from WordNet")
        
        return total_entries
    
    except Exception as e:
        logging.error(f"Error downloading WordNet data: {e}")
        return 0