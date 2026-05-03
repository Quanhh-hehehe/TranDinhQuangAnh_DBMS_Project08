import os
import subprocess
import datetime
import glob
# Sửa lại đường dẫn import cho đúng với cấu trúc: kéo DB_CONFIG từ trong thư mục app ra
from app.config import DB_CONFIG 

class BackupManager:
    def __init__(self):
        # Đặt tên thư mục chứa file backup
        self.backup_dir = "database_backups"
        # Chính sách lưu trữ: Chỉ giữ backup của 7 ngày gần nhất
        self.retention_days = 7 
        
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self):
        """Thực thi lệnh mysqldump để sao lưu toàn bộ Database"""
        print("\n" + "═"*55)
        print("🛡️ HỆ THỐNG SAO LƯU DỮ LIỆU TỰ ĐỘNG (BACKUP) 🛡️".center(55))
        print("═"*55)

        # Tạo tên file theo thời gian thực (VD: Cinema_Backup_20260502_2155.sql)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = os.path.join(self.backup_dir, f"Cinema_Backup_{timestamp}.sql")

        # ⚠️ CHÚ Ý: Đường dẫn mysqldump.exe có thể khác nhau tùy máy của bạn.
        # Nếu chạy báo lỗi không tìm thấy mysqldump, hãy kiểm tra lại đường dẫn cài đặt MySQL này:
        mysqldump_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"

        # Cấu trúc lệnh mysqldump
        dump_cmd = [
            mysqldump_path, 
            f"-h{DB_CONFIG['host']}",
            f"-u{DB_CONFIG['user']}",
            # Mật khẩu lấy thẳng từ file .env (viết dính liền -p theo chuẩn MySQL)
            f"-p{DB_CONFIG['password']}",
            "--routines",          
            "--triggers",          
            "--events",
            "--databases",         
            DB_CONFIG['database']
        ]
        
        try:
            print(f"⏳ Đang tiến hành sao lưu cơ sở dữ liệu '{DB_CONFIG['database']}'...")
            # Thực thi quá trình dump dữ liệu
            with open(backup_file, "w", encoding="utf-8") as outfile:
                subprocess.run(dump_cmd, stdout=outfile, check=True)
            
            file_size = os.path.getsize(backup_file) / 1024 # Tính theo KB
            print(f"✅ THÀNH CÔNG: Đã tạo bản sao lưu an toàn!")
            print(f"📁 Vị trí lưu: {backup_file} ({file_size:.2f} KB)")
            
            # Kích hoạt dọn dẹp các file cũ hơn 7 ngày
            self._cleanup_old_backups()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ LỖI: Không thể sao lưu. Hãy kiểm tra lại quyền truy cập hoặc mật khẩu DB.")
            print(f"Chi tiết: {e}")
        except FileNotFoundError:
            print(f"❌ LỖI: Không tìm thấy công cụ sao lưu tại '{mysqldump_path}'.")
            print("Hãy chắc chắn rằng đường dẫn cài đặt MySQL Server trên máy tính của bạn là chính xác!")

    def _cleanup_old_backups(self):
        """Dọn dẹp các file backup đã quá hạn (Retention Policy)"""
        print(f"🧹 Đang kiểm tra và dọn dẹp các bản backup cũ (Giữ lại {self.retention_days} ngày)...")
        now = datetime.datetime.now()
        
        # Tìm tất cả các file có đuôi .sql trong thư mục backup
        search_pattern = os.path.join(self.backup_dir, "*.sql")
        backup_files = glob.glob(search_pattern)
        
        deleted_count = 0
        for file in backup_files:
            # Lấy thời gian tạo/sửa đổi cuối cùng của file
            file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file))
            age_days = (now - file_creation_time).days
            
            # Xóa nếu vượt quá số ngày quy định
            if age_days > self.retention_days:
                os.remove(file)
                deleted_count += 1
                
        if deleted_count > 0:
            print(f"♻️ Đã dọn dẹp {deleted_count} file backup quá hạn.")
        else:
            print("✨ Không có file backup nào quá hạn cần xóa.")
        print("═"*55)

if __name__ == "__main__":
    bm = BackupManager()
    bm.create_backup()