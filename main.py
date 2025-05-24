import os
import logging
import time

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='dictionary_collection.log'
)

from database import DictionaryDatabase
from collectors.github import download_github_dictionaries
from collectors.opus import download_opus_data
from collectors.wordnet import download_wordnet_data
from collectors.wiktionary import download_wiktionary_data
from enrichment import enrich_data
from utils import timer, print_summary, create_directory, format_time

# Đảm bảo các thư mục cần thiết tồn tại
create_directory("cache")
create_directory("exports")

@timer
def main():
    """Hàm chính để thu thập dữ liệu từ điển"""
    start_time = time.time()
    
    db = DictionaryDatabase()
    
    try:
        print("\n=== ENGLISH-VIETNAMESE & VIETNAMESE-ENGLISH DICTIONARY BUILDER ===\n")
        print("Starting dictionary collection process to gather 300,000+ words...\n")
        
        results = {}
        
        # Method 1: Download from GitHub repositories (fast and reliable)
        print("\n[1/5] Downloading dictionaries from GitHub repositories...")
        github_count = download_github_dictionaries(db)
        results["GitHub Repositories"] = github_count
        print(f"Downloaded {github_count:,} entries from GitHub repositories")
        
        # Method 2: Download from OPUS parallel corpus (good for phrases)
        print("\n[2/5] Downloading from OPUS parallel corpus...")
        opus_count = download_opus_data(db)
        results["OPUS Parallel Corpus"] = opus_count
        print(f"Downloaded {opus_count:,} entries from OPUS parallel corpus")
        
        # Method 3: Download Wiktionary data
        print("\n[3/5] Downloading Wiktionary data...")
        wiktionary_count = download_wiktionary_data(db)
        results["Wiktionary"] = wiktionary_count
        print(f"Downloaded {wiktionary_count:,} entries from Wiktionary")
        
        # Method 4: Import from local CSV files if available
        print("\n[4/5] Checking for local dictionary files...")
        local_count = 0
        
        # Cập nhật để sử dụng module import_from_csv
        if os.path.exists('en_vi_additional.csv'):
            from collectors.local_files import import_from_csv
            local_count += import_from_csv(db, 'en_vi_additional.csv', 'english_vietnamese')
        
        if os.path.exists('vi_en_additional.csv'):
            from collectors.local_files import import_from_csv
            local_count += import_from_csv(db, 'vi_en_additional.csv', 'vietnamese_english')
        
        results["Local Files"] = local_count
        print(f"Imported {local_count:,} entries from local files")
        
        # Final step: Clean and export data
        print("\n[5/5] Cleaning and enriching data...")
        db.remove_duplicates()
        enrich_data(db)
        
        # Final counts
        counts = db.get_counts()
        final_en_vi_count = counts['en_vi']
        final_vi_en_count = counts['vi_en']
        
        # Export to SQL file
        print("\nExporting dictionary to SQL file...")
        export_file = 'exports/dictionary_data.sql'
        db.export_to_sql_file(output_file=export_file)
        
        elapsed_time = time.time() - start_time
        
        # Print summary with formatted counts
        print_summary("COLLECTION SUMMARY", {
            f"English-Vietnamese entries": final_en_vi_count,
            f"Vietnamese-English entries": final_vi_en_count,
            f"Total entries": final_en_vi_count + final_vi_en_count
        }, elapsed_time)
        
        print(f"\nData saved to {export_file}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()