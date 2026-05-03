import os
import getpass

class CinemaView:
    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    # --- 1. MÀN HÌNH CHỌN CỔNG ĐĂNG NHẬP ---
    @staticmethod
    def display_main_portal():
        print("\n" + "═"*55)
        print("🎥 CINEMA ONLINE BOOKING - ENTERPRISE 🎥".center(50))
        print("═"*55)
        print("  1. 👤 Dành cho Khách hàng (Customer Portal)")
        print("  2. 💼 Dành cho Quản lý (Manager Portal)")
        print("  3. 🚪 Thoát ứng dụng (Exit)")
        print("═"*55)

    # --- 2. MENU CỦA KHÁCH HÀNG ---
    @staticmethod
    def display_customer_menu(customer_name):
        print("\n" + "═"*55)
        print(f"👋 XIN CHÀO, {customer_name.upper()}!".center(55))
        print("═"*55)
        print("  1. 📅 Xem lịch chiếu (View Schedule)")
        print("  2. 🎫 Đặt vé trực tuyến (Book Ticket)")
        print("  3. 🔍 Tra cứu & Hủy vé (My Tickets)")
        print("  4. ⚙️ Cập nhật thông tin cá nhân")
        print("  5. 🔙 Đăng xuất (Logout)")
        print("═"*55)

    # --- 3. MENU CỦA QUẢN LÝ ---
    @staticmethod
    def display_manager_menu():
        print("\n" + "═"*55)
        print("💼 BẢNG ĐIỀU KHIỂN QUẢN LÝ (ADMIN DASHBOARD) 💼".center(55))
        print("═"*55)
        print("  1. 📅 Xem lịch chiếu toàn hệ thống")
        print("  2. 📊 Báo cáo Doanh thu & Tỷ lệ lấp đầy")
        print("  3. 🛠️ Quản lý Hệ thống Dữ liệu (CRUD)")
        print("  4. 🔙 Đăng xuất (Logout)")
        print("═"*55)

    @staticmethod
    def display_list(items, title):
        print(f"\n{'-'*10} {title.upper()} {'-'*10}")
        if not items:
            print("⚠️ Không có dữ liệu.")
            return False
            
        for idx, item in enumerate(items, 1):
            if isinstance(item, dict):
                if 'ScreeningTime' in item and 'RoomName' in item and 'TicketID' not in item:
                    print(f" {idx:02d}. [🕒 {item['ScreeningTime']}] - 🚪 Phòng: {item['RoomName']}")
                elif 'TicketID' in item:
                    print(f" {idx:02d}. [🎟️ Mã vé: {item['TicketID']:04d}] Phim: {item['MovieTitle']}")
                    print(f"     => Ngày: {item['ScreeningDate']} | 🕒 {item['ScreeningTime']} | 💺 Ghế: {item['SeatNumber']}")
            else:
                print(f" {idx:02d}. {item}")
        print("-" * (22 + len(title)))
        return True

    @staticmethod
    def display_seat_map(booked_seats, room_name, rows, cols):
        print(f"\n{'='*10} 💺 SƠ ĐỒ GHẾ: {room_name.upper()} {'='*10}")
        print(" Ký hiệu: [ ] = Ghế trống   |   [X] = Đã đặt\n")

        # In thanh tiêu đề cột số (01, 02, 03... đến Max Cột)
        print("     " + " ".join([f"{i:02d}" for i in range(1, cols + 1)]))
        
        # In từng hàng ghế với vòng lặp động
        for r in range(rows):
            row_label = chr(65 + r)
            row_str = f"  {row_label} | "
            for c in range(1, cols + 1):
                seat_id = f"{row_label}{c:02d}"
                row_str += " [X]" if seat_id in booked_seats else " [ ]"
            print(row_str)
            
        print("\n" + " MÀN HÌNH CHÍNH ".center(cols * 4 + 7, "▓") + "\n")   

    @staticmethod
    def show_table(df, title):
        if title:
            print(f"\n>>> {title.upper()} <<<")
        if df.empty:
            print("⚠️ Không có dữ liệu.")
        else:
            print(df.to_string(index=False))

    @staticmethod
    def get_input(prompt):
        return input(prompt)
        
    @staticmethod
    def get_password(prompt):
        return getpass.getpass(prompt)

    @staticmethod
    def show_message(message, success=True):
        prefix = "✅ THÀNH CÔNG" if success else "❌ LỖI"
        print(f"\n{prefix}: {message}")
        
    @staticmethod
    def show_dashboard(df, base_price):
        print("\n" + "★"*70)
        print(" "*15 + "📊 DASHBOARD PHÂN TÍCH DOANH THU & LẤP ĐẦY 📊")
        print(f" "*20 + f"(Giá vé cơ sở áp dụng: {base_price:,.0f} VND)")
        print("★"*70)
        
        if df.empty:
            print("\nChưa có dữ liệu giao dịch nào để thống kê.\n")
        else:
            print("\n" + df.to_string(index=False, justify='center') + "\n")
            
        print("-" * 70)
        print("💡 CHÚ THÍCH HỆ SỐ GIÁ VÉ TỰ ĐỘNG TỪ BẢNG `SeatTypes`:")
        print(" - Rạp IMAX: Giá x 1.5  |  Rạp VIP: Giá x 1.2  |  Rạp COUPLE: Giá x 2.0")
        print("="*70)