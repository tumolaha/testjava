import os
import json
import requests
import time
import random
import logging
from tqdm import tqdm
from config import CACHE_DIR, USER_AGENTS

def download_wiktionary_data(db):
    """Download and process Wiktionary data"""
    print("Downloading Wiktionary data...")
    
    # Create directory for Wiktionary data
    wiktionary_dir = f"{CACHE_DIR}/wiktionary"
    os.makedirs(wiktionary_dir, exist_ok=True)
    
    try:
        # Get Vietnamese words from database
        vietnamese_words = db.get_vietnamese_words(limit=1000)
        
        if not vietnamese_words:
            print("No Vietnamese words found in database, using backup list")
            vi_words_file = f"{CACHE_DIR}/vietnamese-wordlist.txt"
            
            # Try to download a list of Vietnamese words if we don't have any
            if not os.path.exists(vi_words_file):
                try:
                    url = "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet74K.txt"
                    urllib.request.urlretrieve(url, vi_words_file)
                    
                    with open(vi_words_file, 'r', encoding='utf-8') as f:
                        vietnamese_words = [line.strip() for line in f if line.strip()][:1000]
                except:
                    # Fallback to a minimal list
                    vietnamese_words = ["anh", "em", "học", "làm", "người", "thời gian", "công việc", 
                                       "tình yêu", "gia đình", "bạn bè", "trường học", "thành phố"]
        
        print(f"Processing {len(vietnamese_words)} Vietnamese words from Wiktionary")
        
        # Process in smaller batches to avoid overwhelming the API
        batch_size = 20
        entries_en_vi = []
        entries_vi_en = []
        
        for i in range(0, len(vietnamese_words), batch_size):
            batch = vietnamese_words[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(vietnamese_words) + batch_size - 1)//batch_size}")
            
            for vi_word in tqdm(batch, desc="Fetching Wiktionary entries"):
                try:
                    # Use Wiktionary API to get English translations
                    word_for_url = vi_word.replace(' ', '_')
                    api_url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{word_for_url}"
                    cache_file = f"{wiktionary_dir}/{word_for_url.replace('/', '_')}.json"
                    
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        headers = {'User-Agent': random.choice(USER_AGENTS)}
                        response = requests.get(api_url, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            # Cache the result
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False)
                        else:
                            data = None
                    
                    if data and 'vi' in data:
                        for definition in data['vi']:
                            if 'definitions' in definition:
                                for def_item in definition['definitions']:
                                    # Extract English translation if available
                                    en_translation = ""
                                    if 'translations' in def_item:
                                        for trans in def_item['translations']:
                                            if trans.get('language') == 'en' and 'word' in trans:
                                                en_translation = trans['word']
                                                break
                                    
                                    if en_translation:
                                        # Add to Vietnamese-English
                                        entries_vi_en.append({
                                            "vietnamese_word": vi_word,
                                            "english_meaning": en_translation,
                                            "word_type": definition.get('partOfSpeech', ''),
                                            "example": ""
                                        })
                                        
                                        # Add to English-Vietnamese
                                        entries_en_vi.append({
                                            "english_word": en_translation,
                                            "vietnamese_meaning": vi_word,
                                            "word_type": definition.get('partOfSpeech', ''),
                                            "pronunciation": "",
                                            "example": ""
                                        })
                    
                    # Be nice to the API
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.error(f"Error processing Wiktionary data for {vi_word}: {e}")
            
            # Insert batch into database
            if entries_en_vi:
                db.batch_insert_en_vi(entries_en_vi)
                entries_en_vi = []
                
            if entries_vi_en:
                db.batch_insert_vi_en(entries_vi_en)
                entries_vi_en = []
        
        # Get count of entries
        counts = db.get_counts()
        en_vi_count = counts['en_vi']
        vi_en_count = counts['vi_en']
        
        print(f"Total entries after Wiktionary import: {en_vi_count} EN-VI and {vi_en_count} VI-EN")
        
        return en_vi_count + vi_en_count
    
    except Exception as e:
        logging.error(f"Error downloading Wiktionary data: {e}")
        return 0