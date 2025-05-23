import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import logging
from tqdm import tqdm
import pandas as pd
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='dictionary_collection.log'
)

class DictionaryCollector:
    def __init__(self, db_path='dictionary.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.setup_database()
        
        # User agents to avoid being blocked
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
        ]
    
    def setup_database(self):
        """Create the database tables if they don't exist"""
        with open('dictionary_schema.sql', 'r') as f:
            self.cursor.executescript(f.read())
        self.conn.commit()
    
    def get_random_user_agent(self):
        """Return a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def scrape_tflat_dictionary(self, start_page=1, end_page=1000):
        """Scrape TFlat dictionary for English-Vietnamese words"""
        base_url = "https://tflat.vn/tu-dien/tu-vung?page={}"
        
        for page in tqdm(range(start_page, end_page + 1), desc="Scraping TFlat Dictionary"):
            try:
                headers = {'User-Agent': self.get_random_user_agent()}
                response = requests.get(base_url.format(page), headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    word_entries = soup.find_all('div', class_='word-entry')
                    
                    if not word_entries:
                        logging.info(f"No more words found at page {page}, stopping")
                        break
                    
                    for entry in word_entries:
                        try:
                            english_word = entry.find('div', class_='word').text.strip()
                            pronunciation = entry.find('div', class_='pronunciation').text.strip() if entry.find('div', class_='pronunciation') else ""
                            word_type = entry.find('div', class_='type').text.strip() if entry.find('div', class_='type') else ""
                            vietnamese_meaning = entry.find('div', class_='meaning').text.strip()
                            example = entry.find('div', class_='example').text.strip() if entry.find('div', class_='example') else ""
                            
                            self.cursor.execute(
                                "INSERT INTO english_vietnamese (english_word, vietnamese_meaning, word_type, pronunciation, example) VALUES (?, ?, ?, ?, ?)",
                                (english_word, vietnamese_meaning, word_type, pronunciation, example)
                            )
                        except Exception as e:
                            logging.error(f"Error processing word entry: {e}")
                    
                    self.conn.commit()
                    # Random delay to avoid overwhelming the server
                    time.sleep(random.uniform(1, 3))
                else:
                    logging.warning(f"Failed to retrieve page {page}, status code: {response.status_code}")
                    time.sleep(10)  # Longer delay when there's an issue
            except Exception as e:
                logging.error(f"Error scraping page {page}: {e}")
                time.sleep(5)
    
    def scrape_tracau_dictionary(self, num_words=100000):
        """Scrape TracauVN for Vietnamese-English words"""
        # This is a simplified example - actual implementation would need to navigate pagination or search
        base_url = "https://tracau.vn/dictionaries/vietnamese-english/{}"
        
        # List of common Vietnamese search terms to start with
        vietnamese_letters = ["a", "ă", "â", "b", "c", "d", "đ", "e", "ê", "g", "h", "i", "k", "l", "m", "n", "o", "ô", "ơ", "p", "q", "r", "s", "t", "u", "ư", "v", "x", "y"]
        
        word_count = 0
        for letter in vietnamese_letters:
            page = 1
            
            while word_count < num_words:
                try:
                    headers = {'User-Agent': self.get_random_user_agent()}
                    response = requests.get(f"{base_url.format(letter)}?page={page}", headers=headers)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        word_entries = soup.find_all('div', class_='word-item')  # Adjust the selector based on the actual website structure
                        
                        if not word_entries:
                            logging.info(f"No more words found for letter {letter}, moving to next letter")
                            break
                        
                        for entry in word_entries:
                            try:
                                vietnamese_word = entry.find('div', class_='vietnamese').text.strip()
                                english_meaning = entry.find('div', class_='english').text.strip()
                                word_type = entry.find('div', class_='type').text.strip() if entry.find('div', class_='type') else ""
                                example = entry.find('div', class_='example').text.strip() if entry.find('div', class_='example') else ""
                                
                                self.cursor.execute(
                                    "INSERT INTO vietnamese_english (vietnamese_word, english_meaning, word_type, example) VALUES (?, ?, ?, ?)",
                                    (vietnamese_word, english_meaning, word_type, example)
                                )
                                word_count += 1
                            except Exception as e:
                                logging.error(f"Error processing Vietnamese word entry: {e}")
                        
                        self.conn.commit()
                        time.sleep(random.uniform(1, 3))
                        page += 1
                    else:
                        logging.warning(f"Failed to retrieve page for letter {letter}, page {page}, status code: {response.status_code}")
                        break
                except Exception as e:
                    logging.error(f"Error scraping letter {letter}, page {page}: {e}")
                    break
    
    def import_from_wordnet(self, file_path):
        """Import words from Princeton WordNet"""
        # This would require preprocessing the WordNet database
        pass
    
    def import_from_csv(self, csv_path, table_name):
        """Import words from a CSV file"""
        try:
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, self.conn, if_exists='append', index=False)
            logging.info(f"Imported {len(df)} records from {csv_path} to {table_name}")
        except Exception as e:
            logging.error(f"Error importing from CSV: {e}")
    
    def export_to_sql_file(self, output_file='dictionary_data.sql'):
        """Export the database to a .sql file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write schema
                with open('dictionary_schema.sql', 'r') as schema_file:
                    f.write(schema_file.read() + '\n\n')
                
                # Write English-Vietnamese data
                f.write("-- English-Vietnamese data\n")
                self.cursor.execute("SELECT english_word, vietnamese_meaning, word_type, pronunciation, example FROM english_vietnamese")
                rows = self.cursor.fetchall()
                
                for row in rows:
                    english_word, vietnamese_meaning, word_type, pronunciation, example = row
                    # Escape special characters
                    english_word = english_word.replace("'", "''")
                    vietnamese_meaning = vietnamese_meaning.replace("'", "''")
                    word_type = (word_type or "").replace("'", "''")
                    pronunciation = (pronunciation or "").replace("'", "''")
                    example = (example or "").replace("'", "''")
                    
                    f.write(f"INSERT INTO english_vietnamese (english_word, vietnamese_meaning, word_type, pronunciation, example) VALUES ('{english_word}', '{vietnamese_meaning}', '{word_type}', '{pronunciation}', '{example}');\n")
                
                # Write Vietnamese-English data
                f.write("\n-- Vietnamese-English data\n")
                self.cursor.execute("SELECT vietnamese_word, english_meaning, word_type, example FROM vietnamese_english")
                rows = self.cursor.fetchall()
                
                for row in rows:
                    vietnamese_word, english_meaning, word_type, example = row
                    # Escape special characters
                    vietnamese_word = vietnamese_word.replace("'", "''")
                    english_meaning = english_meaning.replace("'", "''")
                    word_type = (word_type or "").replace("'", "''")
                    example = (example or "").replace("'", "''")
                    
                    f.write(f"INSERT INTO vietnamese_english (vietnamese_word, english_meaning, word_type, example) VALUES ('{vietnamese_word}', '{english_meaning}', '{word_type}', '{example}');\n")
                
            logging.info(f"Successfully exported data to {output_file}")
        except Exception as e:
            logging.error(f"Error exporting to SQL file: {e}")
    
    def close(self):
        """Close the database connection"""
        self.conn.close()


# Main execution
if __name__ == "__main__":
    collector = DictionaryCollector()
    
    try:
        # Step 1: Collect English-Vietnamese words
        collector.scrape_tflat_dictionary(start_page=1, end_page=5000)
        
        # Step 2: Collect Vietnamese-English words
        collector.scrape_tracau_dictionary(num_words=300000)
        
        # Step 3: Import from additional sources if available
        if os.path.exists('en_vi_additional.csv'):
            collector.import_from_csv('en_vi_additional.csv', 'english_vietnamese')
        
        if os.path.exists('vi_en_additional.csv'):
            collector.import_from_csv('vi_en_additional.csv', 'vietnamese_english')
        
        # Step 4: Export to SQL file
        collector.export_to_sql_file()
        
        # Check the count of collected words
        collector.cursor.execute("SELECT COUNT(*) FROM english_vietnamese")
        en_vi_count = collector.cursor.fetchone()[0]
        
        collector.cursor.execute("SELECT COUNT(*) FROM vietnamese_english")
        vi_en_count = collector.cursor.fetchone()[0]
        
        logging.info(f"Collected {en_vi_count} English-Vietnamese words")
        logging.info(f"Collected {vi_en_count} Vietnamese-English words")
        
        print(f"Dictionary collection completed:")
        print(f"- {en_vi_count} English-Vietnamese words")
        print(f"- {vi_en_count} Vietnamese-English words")
        print(f"Data saved to dictionary_data.sql")
    
    finally:
        collector.close()