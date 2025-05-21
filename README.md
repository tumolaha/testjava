# testjava

#!/bin/bash

# Cài đặt các gói cần thiết
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib

# Tạo môi trường ảo
python3 -m venv venv
source venv/bin/activate

# Cài đặt các thư viện Python cần thiết
pip install psycopg2-binary requests beautifulsoup4 pandas nltk textblob python-dotenv tqdm

# Tạo cấu trúc thư mục dự án
mkdir -p data/raw data/processed logs scripts

echo "Môi trường đã được thiết lập!"

#!/bin/bash

# Khởi động PostgreSQL
sudo service postgresql start

# Tạo người dùng và cơ sở dữ liệu
sudo -u postgres psql -c "CREATE USER dict_admin WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE dictionary_db OWNER dict_admin;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dictionary_db TO dict_admin;"

# Áp dụng schema
sudo -u postgres psql -d dictionary_db -f dictionary_schema.sql

echo "Cơ sở dữ liệu đã được thiết lập!"


your_secure_password




Hướng dẫn download và setup từ điển để thu thập dữ liệu
Dưới đây là các lệnh chạy để thiết lập và sử dụng hệ thống từ điển của bạn:

1. Tạo thư mục cần thiết
    mkdir -p data/dictionaries data/stardict logs
2. Tải xuống từ điển
            python main.py --download
Lệnh này sẽ tải các từ điển Anh-Việt từ các nguồn trực tuyến. Nếu không tải được, bạn sẽ thấy thông báo hướng dẫn tải thủ công.

3. Kiểm tra từ điển đã tải
    python check_dictionaries.py
Lệnh này sẽ kiểm tra các từ điển đã tải xuống, hiển thị số lượng từ vựng và nguồn gốc của từng từ điển.

4. Áp dụng cấu trúc cơ sở dữ liệu cải tiến
    python main.py --apply-schema
Lệnh này sẽ áp dụng cấu trúc cơ sở dữ liệu cải tiến cho PostgreSQL của bạn.

5. Thu thập dữ liệu từ một từ đơn lẻ
    python main.py -w "example"
Lệnh này sẽ thu thập dữ liệu cho từ "example" và lưu vào cơ sở dữ liệu.

6. Thu thập dữ liệu từ danh sách từ trong file
    python main.py -f "wordlist.txt" -b 50
Trong đó:
    wordlist.txt là file chứa danh sách từ, mỗi từ một dòng
    -b 50 chỉ định xử lý mỗi lần 50 từ (batch size)

7. Thu thập dữ liệu với ưu tiên nguồn cụ thể
    python main.py -w "computer" --priority av
Trong đó:
    --priority av ưu tiên sử dụng nguồn Anh-Việt
    --priority en ưu tiên sử dụng nguồn tiếng Anh

8. Thu thập dữ liệu với nguồn cụ thể
    python main.py -w "language" --sources=StarDict-AV,EVDict
Lệnh này chỉ sử dụng từ điển StarDict-AV và EVDict để thu thập dữ liệu.

9. Thu thập dữ liệu bắt buộc ngay cả khi từ điển có vấn đề
    python main.py -w "hello" --force
Sử dụng cờ --force khi bạn muốn bỏ qua các cảnh báo về chất lượng từ điển.

10. Xuất dữ liệu đã thu thập
    python main.py --output dictionary_export
Lệnh này sẽ xuất dữ liệu từ cơ sở dữ liệu ra file SQL với tên dạng dictionary_export_YYYYMMDD_HHMMSS.sql.