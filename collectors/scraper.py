import os
import json
import requests
import random
import time
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from config import CACHE_DIR, USER_AGENTS

def scrape_tflat_dictionary_parallel(db, start_page=1, end_page=100, max_workers=5):
    """Scrape TFlat dictionary with parallel processing"""
    print(f"Scraping TFlat dictionary (pages {start_page}-{end_page})...")
    base_url = "https://tflat.vn/tu-dien/tu-vung?page={}"
    
    total_entries = 0
    
    # Function to scrape a single page
    def scrape_page(page):
        cache_file = f"{CACHE_DIR}/tflat_page_{page}.json"
        
        # Check if page is already cached
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading cache for page {page}: {e}")
        
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(base_url.format(page), headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                word_entries = soup.find_all('div', class_='word-entry')
                
                if not word_entries:
                    return []
                
                page_results = []
                for entry in word_entries:
                    try:
                        english_word = entry.find('div', class_='word').text.strip()
                        pronunciation = entry.find('div', class_='pronunciation').text.strip() if entry.find('div', class_='pronunciation') else ""
                        word_type = entry.find('div', class_='type').text.strip() if entry.find('div', class_='type') else ""
                        vietnamese_meaning = entry.find('div', class_='meaning').text.strip()
                        example = entry.find('div', class_='example').text.strip() if entry.find('div', class_='example') else ""
                        
                        page_results.append({
                            "english_word": english_word,
                            "vietnamese_meaning": vietnamese_meaning,
                            "word_type": word_type,
                            "pronunciation": pronunciation,
                            "example": example
                        })
                    except Exception as e:
                        logging.error(f"Error processing entry on page {page}: {e}")
                
                # Cache the results
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(page_results, f, ensure_ascii=False)
                
                time.sleep(random.uniform(0.5, 1))
                return page_results
            else:
                logging.warning(f"Failed to get page {page}, status: {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"Error scraping page {page}: {e}")
            return []
    
    # Process pages in batches to manage memory
    batch_size = 20
    
    for batch_start in range(start_page, end_page + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_page)
        print(f"Processing batch: pages {batch_start}-{batch_end}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {executor.submit(scrape_page, page): page for page in range(batch_start, batch_end + 1)}
            
            all_entries = []
            for future in tqdm(as_completed(future_to_page), total=len(future_to_page), desc="Scraping pages"):
                page_entries = future.result()
                all_entries.extend(page_entries)
        
        # Insert batch into database
        if all_entries:
            count = db.batch_insert_en_vi(all_entries)
            total_entries += count
            print(f"Collected {count} entries from batch {batch_start}-{batch_end}")
    
    return total_entries

def scrape_tracau_dictionary(db, limit=10000):
    """Scrape TracauVN for Vietnamese-English words"""
    print(f"Scraping TracauVN dictionary (limit: {limit} words)...")
    base_url = "https://tracau.vn/dictionaries/vietnamese-english/{}"
    
    # List of Vietnamese letters to search
    vietnamese_letters = ["a", "ă", "â", "b", "c", "d", "đ", "e", "ê", "g", "h", "i", "k", 
                          "l", "m", "n", "o", "ô", "ơ", "p", "q", "r", "s", "t", "u", "ư", "v", "x", "y"]
    
    total_entries = 0
    
    for letter in vietnamese_letters:
        if total_entries >= limit:
            break
            
        print(f"Processing words starting with '{letter}'...")
        page = 1
        letter_entries = []
        
        while total_entries < limit:
            cache_file = f"{CACHE_DIR}/tracau_{letter}_page_{page}.json"
            
            # Check cache
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        page_entries = json.load(f)
                        if not page_entries:
                            break
                        letter_entries.extend(page_entries)
                        page += 1
                        continue
                except Exception as e:
                    logging.error(f"Error loading cache for {letter} page {page}: {e}")
            
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(f"{base_url.format(letter)}?page={page}", headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    word_entries = soup.find_all('div', class_='word-item')  # Adjust selector as needed
                    
                    if not word_entries:
                        print(f"No more words found for letter {letter}")
                        break
                    
                    page_entries = []
                    for entry in word_entries:
                        try:
                            vietnamese_word = entry.find('div', class_='vietnamese').text.strip()
                            english_meaning = entry.find('div', class_='english').text.strip()
                            word_type = entry.find('div', class_='type').text.strip() if entry.find('div', class_='type') else ""
                            example = entry.find('div', class_='example').text.strip() if entry.find('div', class_='example') else ""
                            
                            page_entries.append({
                                "vietnamese_word": vietnamese_word,
                                "english_meaning": english_meaning,
                                "word_type": word_type,
                                "example": example
                            })
                        except Exception as e:
                            logging.error(f"Error processing word entry for letter {letter}, page {page}: {e}")
                    
                    # Cache the results
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(page_entries, f, ensure_ascii=False)
                    
                    letter_entries.extend(page_entries)
                    page += 1
                    time.sleep(random.uniform(1, 2))
                else:
                    print(f"Failed to get page {page} for letter {letter}, status: {response.status_code}")
                    break
                    
            except Exception as e:
                logging.error(f"Error scraping letter {letter}, page {page}: {e}")
                break
        
        # Insert batch into database
        if letter_entries:
            count = db.batch_insert_vi_en(letter_entries)
            total_entries += count
            print(f"Collected {count} Vietnamese-English entries for letter '{letter}'")
    
    return total_entries