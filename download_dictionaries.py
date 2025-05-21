import os
import requests
import logging
import zipfile
import tarfile
import gzip
import shutil
import time
from tqdm import tqdm

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('dict_downloader')

def download_file(url, output_path, logger, retry=3):
    """Tải file với khả năng thử lại"""
    for attempt in range(retry):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                for chunk in tqdm(
                    response.iter_content(chunk_size=8192), 
                    total=total_size//8192 if total_size > 0 else None, 
                    unit='KB',
                    desc=os.path.basename(output_path)
                ):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Đã tải xong file {output_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Lần {attempt+1}/{retry}: Lỗi khi tải file {url}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            
            if attempt < retry - 1:
                wait_time = 2 ** attempt  # Chờ tăng dần: 1, 2, 4, 8... giây
                logger.info(f"Chờ {wait_time} giây trước khi thử lại...")
                time.sleep(wait_time)
            
    logger.error(f"Đã thử {retry} lần nhưng không thể tải file {url}")
    return False

def extract_archive(archive_path, extract_to, logger):
    """Giải nén file nén"""
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        
        elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
        
        elif archive_path.endswith('.gz') and not archive_path.endswith('.tar.gz'):
            # Giải nén file .gz (không phải .tar.gz)
            output_path = archive_path[:-3]  # Xóa .gz
            with gzip.open(archive_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.write(f_in.read())
        
        logger.info(f"Đã giải nén file {archive_path}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi giải nén file {archive_path}: {e}")
        return False

def find_dict_files(dir_path, logger):
    """Tìm tất cả các file từ điển trong thư mục và thư mục con"""
    dict_files = []
    
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.dict.dz') or file.endswith('.dict'):
                dict_path = os.path.join(root, file)
                ifo_path = os.path.join(root, file.replace('.dict.dz', '.ifo').replace('.dict', '.ifo'))
                
                dict_files.append({
                    'dict': dict_path,
                    'ifo': ifo_path if os.path.exists(ifo_path) else None,
                    'name': os.path.basename(file).split('.')[0]
                })
    
    logger.info(f"Tìm thấy {len(dict_files)} file từ điển trong {dir_path}")
    return dict_files

def show_dictionary_download_instructions(logger):
    """Hiển thị hướng dẫn tải từ điển có chất lượng cao"""
    logger.warning("\n===== HƯỚNG DẪN TẢI TỪ ĐIỂN ANH-VIỆT =====")
    logger.warning("Không thể tải từ điển tự động. Hãy thử các cách sau:")
    
    logger.warning("\n1. TẢI TỪ ĐIỂN TỪ CÁC NGUỒN CHÍNH THỨC:")
    logger.warning("   - StarDict Anh-Việt: https://sourceforge.net/projects/stardict-4/files/dictionaries/")
    logger.warning("   - Từ điển Lạc Việt: http://www.lacviet.com.vn/")
    logger.warning("   - Từ điển Hồ Ngọc Đức: https://www.informatik.uni-leipzig.de/~duc/Dict/")
    
    logger.warning("\n2. TẢI TỪ CÁC KHO LƯU TRỮ GITHUB:")
    logger.warning("   - git clone https://github.com/open-dict-data/ding-dictionary")
    logger.warning("   - git clone https://github.com/1ec5/evdict")
    
    logger.warning("\n3. CHUYỂN ĐỔI TỪ CÁC ĐỊNH DẠNG KHÁC:")
    logger.warning("   - Sử dụng công cụ: https://github.com/huzheng001/stardict-tools")
    logger.warning("   - Định dạng Babylon (BGL): babylon -s để chuyển đổi sang StarDict")
    logger.warning("   - Định dạng XDXF: xdxf2stardict để chuyển đổi sang StarDict")
    
    logger.warning("\n4. SỬ DỤNG CÁC TỪ ĐIỂN TRỰC TUYẾN:")
    logger.warning("   - https://vdict.com")
    logger.warning("   - https://dict.laban.vn")
    logger.warning("   - https://www.informatik.uni-leipzig.de/~duc/Dict/")
    
    logger.warning("\nSau khi tải về, đặt các file từ điển vào thư mục:")
    logger.warning("   data/dictionaries/ hoặc data/stardict/")
    logger.warning("\nCác file cần thiết cho một từ điển StarDict:")
    logger.warning("   - *.dict hoặc *.dict.dz: File dữ liệu chính")
    logger.warning("   - *.idx: File chỉ mục")
    logger.warning("   - *.ifo: File thông tin")
    
    logger.warning("\nLƯU Ý: Từ điển chất lượng cao thường có kích thước từ 5MB đến vài trăm MB")
    logger.warning("      và chứa từ 50,000 đến hơn 300,000 từ.")
    logger.warning("=================================================\n")

def main():
    logger = setup_logging()
    logger.info("Bắt đầu tải từ điển Anh-Việt chính thức")
    
    # Thư mục lưu trữ
    dict_dir = 'data/dictionaries'
    temp_dir = 'data/temp'
    
    # Tạo thư mục cần thiết
    os.makedirs(dict_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Nguồn từ điển chính thức (cập nhật URL thực tế)
    dict_sources = [
        # FreeDict
        {
            'name': 'FreeDict-EnVi',
            'url': 'https://download.freedict.org/dictionaries/eng-vie/eng-vie_dictd.tar.gz',
            'type': 'archive'
        },
        # EVDict
        {
            'name': 'EVDict',
            'url': 'https://evdict.com/download/EVDict-data.tar.gz',
            'type': 'archive'
        },
        # StarDict English-Vietnamese  
        {
            'name': 'StarDict-EnVi',
            'url': 'https://sourceforge.net/projects/xdxf/files/dicts-stardict-form/english-to-viet/DIC_ENVI.zip',
            'type': 'archive'
        },
        # VDict
        {
            'name': 'VDict',
            'url': 'https://vdict.com/download/vdict-data.zip',
            'type': 'archive'
        }
    ]
    
    # Tải và xử lý từng nguồn từ điển
    downloaded_sources = []
    
    for source in dict_sources:
        logger.info(f"Đang tải xuống từ điển {source['name']}...")
        
        if source['type'] == 'archive':
            # Tải file nén
            archive_path = os.path.join(temp_dir, f"{source['name']}.{source['url'].split('.')[-1]}")
            
            if download_file(source['url'], archive_path, logger):
                # Tạo thư mục giải nén riêng cho nguồn này
                extract_dir = os.path.join(temp_dir, source['name'])
                os.makedirs(extract_dir, exist_ok=True)
                
                # Giải nén file
                if extract_archive(archive_path, extract_dir, logger):
                    # Tìm các file từ điển trong thư mục giải nén
                    dict_files = find_dict_files(extract_dir, logger)
                    
                    if dict_files:
                        # Di chuyển các file từ điển vào thư mục chính
                        for dict_file in dict_files:
                            # Tạo tên file đích có tiền tố là nguồn
                            dest_dict = os.path.join(dict_dir, f"{source['name']}-{os.path.basename(dict_file['dict'])}")
                            shutil.copy2(dict_file['dict'], dest_dict)
                            
                            if dict_file['ifo']:
                                dest_ifo = os.path.join(dict_dir, f"{source['name']}-{os.path.basename(dict_file['ifo'])}")
                                shutil.copy2(dict_file['ifo'], dest_ifo)
                                
                            # Kiểm tra file idx nếu có
                            idx_path = dict_file['dict'].replace('.dict.dz', '.idx').replace('.dict', '.idx')
                            if os.path.exists(idx_path):
                                dest_idx = os.path.join(dict_dir, f"{source['name']}-{os.path.basename(idx_path)}")
                                shutil.copy2(idx_path, dest_idx)
                                
                        downloaded_sources.append({
                            'name': source['name'],
                            'files': dict_files,
                            'path': dict_dir
                        })
                        logger.info(f"Đã sao chép các file từ điển từ {source['name']}")
                    else:
                        # Không tìm thấy file từ điển, di chuyển toàn bộ thư mục
                        dest_dir = os.path.join(dict_dir, source['name'])
                        if os.path.exists(dest_dir):
                            shutil.rmtree(dest_dir)
                        shutil.copytree(extract_dir, dest_dir)
                        logger.info(f"Đã sao chép thư mục từ điển {source['name']}")
        
        elif source['type'] == 'file':
            # Tải trực tiếp file
            output_file = source.get('output', os.path.basename(source['url']))
            output_path = os.path.join(dict_dir, output_file)
            
            if download_file(source['url'], output_path, logger):
                downloaded_sources.append({
                    'name': source['name'],
                    'file': output_path,
                    'path': dict_dir
                })
                logger.info(f"Đã tải file từ điển {source['name']}")
    
    # Tạo báo cáo tải xuống
    logger.info("\n=== BÁO CÁO TẢI XUỐNG ===")
    logger.info(f"Số nguồn đã tải: {len(downloaded_sources)}/{len(dict_sources)}")
    
    for i, source in enumerate(downloaded_sources, 1):
        logger.info(f"{i}. {source['name']}")
        if 'files' in source:
            for f in source['files']:
                logger.info(f"   - {f['name']}")
    
    # Nếu không tải được từ điển
    github_success = False  # Placeholder for actual GitHub success check
    wordnet_success = False  # Placeholder for actual WordNet success check
    if not github_success and not wordnet_success and not downloaded_sources:
        logger.warning("Không thể tải xuống từ điển từ bất kỳ nguồn nào.")
        show_dictionary_download_instructions(logger)
        
        # Tạo file README hướng dẫn trong thư mục từ điển
        readme_path = os.path.join(dict_dir, "README_DICTIONARY.txt")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("HƯỚNG DẪN TẢI TỪ ĐIỂN ANH-VIỆT\n")
            f.write("===============================\n\n")
            f.write("Thư mục này dùng để lưu trữ từ điển StarDict Anh-Việt.\n\n")
            f.write("Bạn cần tải về các file từ điển có định dạng:\n")
            f.write("- *.dict hoặc *.dict.dz: File dữ liệu chính\n")
            f.write("- *.idx: File chỉ mục\n")
            f.write("- *.ifo: File thông tin\n\n")
            f.write("Các nguồn tải từ điển chất lượng cao:\n")
            f.write("1. StarDict Anh-Việt: https://sourceforge.net/projects/stardict-4/files/dictionaries/\n")
            f.write("2. Từ điển Lạc Việt: http://www.lacviet.com.vn/\n")
            f.write("3. Từ điển Hồ Ngọc Đức: https://www.informatik.uni-leipzig.de/~duc/Dict/\n")
            f.write("4. GitHub: https://github.com/open-dict-data/ding-dictionary\n\n")
            f.write("Lưu ý: Từ điển chất lượng cao thường có kích thước từ 5MB đến vài trăm MB\n")
            f.write("và chứa từ 50,000 đến hơn 300,000 từ.\n")
        
        logger.info(f"Đã tạo file hướng dẫn tại: {readme_path}")
    
    # Dọn dẹp thư mục tạm
    shutil.rmtree(temp_dir, ignore_errors=True)
    logger.info("Đã dọn dẹp thư mục tạm")
    logger.info("Quá trình tải xuống từ điển hoàn tất")

if __name__ == "__main__":
    main()