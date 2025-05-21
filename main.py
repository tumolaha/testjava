import argparse
import logging
from datetime import datetime
import os
from dictionary_manager import DictionaryManager

def setup_logging():
    """Thiết lập logging"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = f"{log_dir}/dictionary_collector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Cũng ghi log ra console
        ]
    )
    
    return logging.getLogger('main')

def parse_arguments():
    """Phân tích tham số dòng lệnh"""
    parser = argparse.ArgumentParser(description='Công cụ thu thập dữ liệu từ điển Anh-Việt')
    
    parser.add_argument('-w', '--word', help='Từ cần thu thập')
    parser.add_argument('-f', '--file', help='File chứa danh sách từ cần thu thập')
    parser.add_argument('-b', '--batch-size', type=int, default=50, help='Kích thước batch')
    parser.add_argument('-o', '--output', default='dictionary_export', help='Tên file SQL đầu ra')
    parser.add_argument('--download', action='store_true', help='Tải về từ điển Anh-Việt')
    parser.add_argument('--apply-schema', action='store_true', help='Áp dụng cấu trúc cơ sở dữ liệu cải tiến')
    parser.add_argument('--priority', choices=['av', 'en'], default='av', 
                        help='Ưu tiên nguồn dữ liệu (av: Anh-Việt, en: tiếng Anh)')
    parser.add_argument('--sources', help='Danh sách nguồn dữ liệu sử dụng (phân cách bằng dấu phẩy)')
    parser.add_argument('--force', action='store_true', 
                        help='Bắt buộc tiếp tục ngay cả khi từ điển không đủ chất lượng')
    parser.add_argument('--skip-quality-check', action='store_true',
                        help='Bỏ qua kiểm tra chất lượng từ điển')
    
    return parser.parse_args()

def main():
    """Hàm chính"""
    logger = setup_logging()
    args = parse_arguments()
    
    # Áp dụng cấu trúc cơ sở dữ liệu cải tiến nếu được yêu cầu
    if args.apply_schema:
        from database.db_connector import DatabaseConnector
        logger.info("Đang áp dụng cấu trúc cơ sở dữ liệu cải tiến...")
        db = DatabaseConnector()
        if db.connect():
            if db.apply_improved_schema():
                logger.info("Đã áp dụng cấu trúc cơ sở dữ liệu cải tiến thành công")
            else:
                logger.error("Không thể áp dụng cấu trúc cơ sở dữ liệu cải tiến")
            db.disconnect()
        else:
            logger.error("Không thể kết nối đến cơ sở dữ liệu")
    
    # Tải từ điển nếu được yêu cầu
    if args.download:
        logger.info("Đang tải xuống từ điển Anh-Việt...")
        from download_dictionaries import main as download_dicts
        download_dicts()
    
    if not args.word and not args.file and not args.download and not args.apply_schema:
        logger.error("Phải cung cấp từ cần thu thập (-w), file danh sách từ (-f), tải từ điển (--download) hoặc áp dụng schema (--apply-schema)")
        return 1
    
    # Nếu chỉ tải từ điển hoặc áp dụng schema mà không xử lý từ, kết thúc
    if (args.download or args.apply_schema) and not args.word and not args.file:
        return 0
    
    # Thêm tùy chọn để bỏ qua việc kiểm tra chất lượng từ điển
    if args.skip_quality_check:
        logger.info("Bỏ qua kiểm tra chất lượng từ điển theo yêu cầu")
    
    try:
        logger.info("Bắt đầu thu thập dữ liệu từ điển")
        manager = DictionaryManager()
        
        # Kiểm tra chất lượng từ điển và cảnh báo nếu cần
        if not args.skip_quality_check:
            quality_ok = manager.check_dictionary_quality()
            if not quality_ok:
                logger.warning("Từ điển có thể không đủ chất lượng cho việc thu thập dữ liệu chính xác")
                if not args.force:
                    logger.warning("Sử dụng --force để bỏ qua cảnh báo này")
                    logger.info("Quá trình thu thập dữ liệu đã bị hủy")
                    return 1
                else:
                    logger.warning("Tiếp tục thu thập dữ liệu với từ điển không đủ chất lượng (--force)")
        
        # Thiết lập ưu tiên thu thập dữ liệu
        if args.priority == 'en':
            logger.info("Cấu hình: Ưu tiên thu thập từ nguồn tiếng Anh")
            # Vô hiệu hóa các scraper Anh-Việt
            if hasattr(manager, 'vdict'):
                manager.vdict = None
            if hasattr(manager, 'stardict_av'):
                manager.stardict_av = None
        else:
            logger.info("Cấu hình: Ưu tiên thu thập từ nguồn Anh-Việt")
        
        # Giới hạn nguồn dữ liệu nếu cần
        if args.sources:
            source_list = args.sources.split(',')
            logger.info(f"Giới hạn nguồn dữ liệu: {', '.join(source_list)}")
            # Vô hiệu hóa các nguồn không được chọn
            # (Thực hiện theo logic riêng của DictionaryManager)
        
        if args.word:
            # Xử lý một từ
            logger.info(f"Đang xử lý từ: {args.word}")
            word_id = manager.process_word(args.word)
            if word_id:
                logger.info(f"Đã xử lý thành công từ '{args.word}' với ID {word_id}")
            else:
                logger.warning(f"Không thể xử lý từ '{args.word}'")
        
        if args.file:
            # Xử lý danh sách từ từ file
            logger.info(f"Đang xử lý danh sách từ từ file: {args.file}")
            results = manager.process_word_file(args.file, args.batch_size)
            
            # Báo cáo kết quả
            total = len(results)
            successful = sum(1 for _, success in results if success)
            logger.info(f"Kết quả: {successful}/{total} từ thành công ({successful/total*100:.2f}%)")
        
        # Xuất dữ liệu ra file SQL
        logger.info("Đang xuất cơ sở dữ liệu ra file SQL")
        success, filename = manager.export_to_sql(args.output)
        
        if success:
            logger.info(f"Đã xuất thành công ra file: {filename}")
        else:
            logger.error("Xuất dữ liệu thất bại")
        
        # Đóng kết nối
        manager.close()
        logger.info("Quá trình thu thập dữ liệu hoàn tất")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Lỗi không xử lý được: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)