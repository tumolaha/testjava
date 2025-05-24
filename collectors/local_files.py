import pandas as pd
import logging
from processors.csv import process_en_vi_csv, process_vi_en_csv

def import_from_csv(db, csv_path, table_name):
    """Import words from a CSV file into the database"""
    print(f"Importing from CSV: {csv_path}")
    
    try:
        if table_name == 'english_vietnamese':
            entries = process_en_vi_csv(csv_path)
            count = db.batch_insert_en_vi(entries)
        elif table_name == 'vietnamese_english':
            entries = process_vi_en_csv(csv_path)
            count = db.batch_insert_vi_en(entries)
        else:
            print(f"Unknown table: {table_name}")
            return 0
        
        print(f"Imported {count} entries from {csv_path}")
        return count
        
    except Exception as e:
        logging.error(f"Error importing from CSV {csv_path}: {e}")
        print(f"Error importing from CSV {csv_path}: {e}")
        return 0