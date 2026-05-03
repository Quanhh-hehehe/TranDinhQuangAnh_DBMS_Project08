import re
import logging
from .models import CinemaModel
from .views import CinemaView

class CinemaController:
    def __init__(self):
        self.model = CinemaModel()
        self.view = CinemaView()
        # Biến quản lý phiên đăng nhập (Session)
        self.current_user = None 

    def _get_menu_choice(self, prompt):
        """Hỗ trợ nhập 01, 02... và xóa khoảng trắng"""
        raw = self.view.get_input(prompt).strip()
        try:
            return str(int(raw)) # '02' -> 2 -> '2'
        except:
            return raw

    def get_valid_idx(self, items, prompt):
        """Giữ người dùng ở lại danh sách nếu nhập sai, hỗ trợ 01, 02"""
        while True:
            raw = self.view.get_input(prompt).strip()
            if raw == '0': return -1
            try:
                val = int(raw)
                if 1 <= val <= len(items):
                    return val - 1
            except:
                pass
            self.view.show_message("Lựa chọn không hợp lệ! Vui lòng nhập lại số thứ tự trong danh sách.", False)

    def start(self):
        # MÀN HÌNH CỔNG CHÍNH (MAIN PORTAL)
        while True:
            self.view.clear_screen()
            self.view.display_main_portal()
            choice = self._get_menu_choice("Chọn cổng truy cập (1-3): ")
            
            if choice == '1': 
                self.customer_flow()
            elif choice == '2': 
                self.manager_flow()
            elif choice == '3':
                print("\nTạm biệt! Hẹn gặp lại.")
                break
            else:
                self.view.show_message("Lựa chọn không hợp lệ. Vui lòng nhập số từ 1 đến 3.", False)
                self.view.get_input("Nhấn Enter để tiếp tục...")

    # ==========================================
    # LUỒNG 1: DÀNH CHO KHÁCH HÀNG (CUSTOMER PORTAL)
    # ==========================================
    def customer_flow(self):
        self.current_user = self._authenticate_user()
        if not self.current_user:
            return 
            
        while True:
            self.view.clear_screen()
            # Chỉ gọi duy nhất 1 lệnh hiển thị menu từ View
            self.view.display_customer_menu(self.current_user['CustomerName'])
            
            choice = self._get_menu_choice("Chọn chức năng (1-5): ")
            
            if choice == '1': 
                self.handle_view_schedule(is_manager=False)
            elif choice == '2': 
                self.handle_online_booking() 
            elif choice == '3': 
                self.handle_cancel_ticket()  
            elif choice == '4':
                self.handle_update_profile()
            elif choice == '5':
                logging.info(f"Khách hàng '{self.current_user['Username']}' đã đăng xuất.")
                self.current_user = None 
                self.view.show_message("Đã đăng xuất thành công!")
                self.view.get_input("Nhấn Enter để về Cổng chính...")
                break
            else:
                self.view.show_message("Lựa chọn không hợp lệ.", False)
                self.view.get_input("Nhấn Enter để tiếp tục...")
                
    def handle_update_profile(self):
        """Màn hình khách hàng tự sửa thông tin (Có Validate)"""
        self.view.clear_screen()
        cust = self.current_user
        print(f"\n--- ⚙️ CẬP NHẬT THÔNG TIN: {cust['CustomerName']} ---")
        print("(💡 Mẹo: Nhấn Enter để giữ nguyên thông tin cũ, gõ '0' để HỦY TOÀN BỘ)\n")
        
        # Lấy lại thông tin đầy đủ từ DB để có phone hiện tại
        full_info = self.model.get_customer_by_username(cust['Username'])
        current_phone = full_info.get('PhoneNumber', 'Chưa có') 
        
        # 1. XỬ LÝ NHẬP HỌ TÊN
        while True:
            new_name = self.view.get_input(f"Họ tên mới [{cust['CustomerName']}]: ").strip()
            if new_name == '0': 
                self.view.show_message("Đã hủy cập nhật thông tin.", False)
                self.view.get_input("\nNhấn Enter để quay lại...")
                return
            if not new_name: # Nếu nhấn Enter -> Giữ nguyên tên cũ
                new_name = cust['CustomerName']
                break
            break # Có nhập tên mới -> Thoát vòng lặp
            
        # 2. XỬ LÝ NHẬP SỐ ĐIỆN THOẠI
        while True:
            new_phone = self.view.get_input(f"Số điện thoại mới [{current_phone}]: ").strip()
            if new_phone == '0':
                self.view.show_message("Đã hủy cập nhật thông tin.", False)
                self.view.get_input("\nNhấn Enter để quay lại...")
                return
            if not new_phone: # Nếu nhấn Enter -> Giữ nguyên số cũ
                new_phone = current_phone
                break
            if not re.match(r'^0\d{9}$', new_phone): # Kiểm tra chuẩn định dạng VN
                self.view.show_message("Số điện thoại không hợp lệ! (Bắt buộc phải có đúng 10 chữ số và bắt đầu bằng số 0)", False)
                continue # Sai định dạng -> Bắt vòng lại nhập tiếp
            break

        # 3. XỬ LÝ NHẬP MẬT KHẨU
        new_pwd = None
        change_pass = self.view.get_input("\nBạn có muốn đổi mật khẩu không? (y/n hoặc '0' để hủy): ").strip().lower()
        
        if change_pass == '0':
            self.view.show_message("Đã hủy cập nhật thông tin.", False)
            self.view.get_input("\nNhấn Enter để quay lại...")
            return
            
        if change_pass == 'y':
            while True:
                pwd_input = self.view.get_password("Nhập mật khẩu mới (hoặc '0' để hủy): ").strip()
                if pwd_input == '0':
                    self.view.show_message("Đã hủy cập nhật thông tin.", False)
                    self.view.get_input("\nNhấn Enter để quay lại...")
                    return
                if not pwd_input:
                    self.view.show_message("Mật khẩu mới không được để trống!", False)
                    continue # Bắt vòng lại nhập tiếp
                new_pwd = pwd_input
                break
        
        # 4. TIẾN HÀNH CẬP NHẬT
        try:
            self.model.update_customer_profile(cust['CustomerID'], new_name, new_phone, new_pwd)
            self.current_user['CustomerName'] = new_name # Cập nhật session tạm thời
            logging.info(f"Khách hàng '{cust['Username']}' đã cập nhật thông tin hồ sơ thành công.")
            self.view.show_message("Cập nhật thông tin cá nhân thành công!")
        except Exception as e:
            self.view.show_message("Lỗi: Số điện thoại này đã được người khác sử dụng!", False)
            
        self.view.get_input("\nNhấn Enter để tiếp tục...")

    # ==========================================
    # LUỒNG 2: DÀNH CHO QUẢN LÝ (MANAGER PORTAL)
    # ==========================================
    def manager_flow(self):
        current_role = None 
        
        while True:
            self.view.clear_screen()
            print("\n--- 💼 CỔNG QUẢN TRỊ VIÊN ---")
            
            username = self.view.get_input("Tên đăng nhập Quản lý (hoặc '0' để về Cổng chính): ").strip()
            if username == '0': return
            
            pwd = self.view.get_password("Mật khẩu Quản lý (hoặc '0' để quay lại sửa Tên đăng nhập): ")
            if pwd == '0': 
                continue 
            
            try:
                staff = self.model.get_staff_by_username(username)
            except Exception as e:
                self.view.show_message("LỖI CƠ SỞ DỮ LIỆU: Vui lòng kiểm tra kết nối!", False)
                return

            if staff and self.model.verify_password(pwd, staff.get('Password')):
                current_role = staff.get('Role')
                logging.info(f"Quản lý/Nhân viên '{username}' ({current_role}) đã đăng nhập hệ thống.")
                self.view.show_message(f"Xác thực thành công! Xin chào: {staff['FullName']} ({current_role})")
                self.view.get_input("Nhấn Enter để vào Bảng điều khiển...")
                break 
            else:
                logging.warning(f"CẢNH BÁO BẢO MẬT: Có người cố gắng đăng nhập sai mật khẩu Quản lý với tài khoản '{username}'")
                self.view.show_message("Sai tên đăng nhập hoặc mật khẩu! Cảnh báo truy cập trái phép.", False)
                self.view.get_input("Nhấn Enter để tiếp tục...")
        
        while True:
            self.view.clear_screen()
            # Chỉ gọi duy nhất 1 lệnh hiển thị menu từ View
            self.view.display_manager_menu()
            
            choice = self._get_menu_choice("Chọn chức năng (1-4): ")
            
            if choice == '1': 
                self.handle_view_schedule(is_manager=True)
            elif choice == '2': 
                if current_role == 'Manager':
                    self.handle_revenue_report()
                else:
                    self.view.show_message("TỪ CHỐI TRUY CẬP: Chỉ Quản lý rạp mới được xem Báo cáo Doanh thu!", False)
                    self.view.get_input("\nNhấn Enter để quay lại...")
            elif choice == '3':
                self.handle_data_management(current_role)
            elif choice == '4':
                logging.info(f"Quản lý/Nhân viên '{username}' đã đăng xuất.")
                self.view.show_message("Đã đăng xuất khỏi phiên Quản lý!")
                self.view.get_input("Nhấn Enter để về Cổng chính...")
                break
            else:
                self.view.show_message("Lựa chọn không hợp lệ.", False)
                self.view.get_input("Nhấn Enter để tiếp tục...")

    # ==========================================
    # CÁC HÀM XỬ LÝ NGHIỆP VỤ (CORE LOGIC)
    # ==========================================
    def _authenticate_user(self):
        while True:
            self.view.clear_screen()
            print("\n--- 👤 ĐĂNG NHẬP KHÁCH HÀNG ---")
            username = self.view.get_input("Nhập Tên đăng nhập (hoặc '0' để về Cổng chính): ").strip()
            if username == '0': return None
            if not username:
                self.view.show_message("Tên đăng nhập không được để trống!", False)
                self.view.get_input("Nhấn Enter để thử lại...")
                continue
            
            try:
                customer = self.model.get_customer_by_username(username)
            except Exception as e:
                self.view.show_message("LỖI CƠ SỞ DỮ LIỆU: Vui lòng kiểm tra kết nối!", False)
                return None

            if customer:
                while True:
                    pwd = self.view.get_password("Nhập mật khẩu (hoặc '0' để quay lại sửa Tên đăng nhập): ")
                    if pwd == '0': 
                        break 
                    
                    if self.model.verify_password(pwd, customer.get('Password')):
                        customer['Username'] = username 
                        logging.info(f"Khách hàng '{username}' đăng nhập thành công.")
                        return customer
                    else:
                        logging.warning(f"Đăng nhập thất bại: Khách hàng '{username}' nhập sai mật khẩu.")
                        self.view.show_message("Sai mật khẩu! Vui lòng thử lại.", False)
            else:
                print("\nTên đăng nhập chưa tồn tại. Hãy tạo tài khoản mới!")
                reg_step = 1
                name = ""
                phone = ""
                pwd = ""
                cancel_registration = False

                while reg_step <= 3:
                    if reg_step == 1:
                        name = self.view.get_input("Nhập họ tên đầy đủ (hoặc '0' để quay lại đổi Tên đăng nhập): ").strip()
                        if name == '0': 
                            cancel_registration = True
                            break
                        if not name:
                            self.view.show_message("Tên không được để trống!", False)
                        else:
                            reg_step = 2 
                            
                    elif reg_step == 2:
                        phone = self.view.get_input("Nhập số điện thoại (hoặc '0' để LÙI LẠI sửa Họ Tên): ").strip()
                        if phone == '0': 
                            reg_step = 1 
                        elif not phone:
                            self.view.show_message("Số điện thoại không được để trống!", False)
                        elif not re.match(r'^0\d{9}$', phone):
                            self.view.show_message("Số điện thoại không hợp lệ! (Bắt buộc phải có đúng 10 chữ số và bắt đầu bằng số 0)", False)
                        else:
                            reg_step = 3 
                            
                    elif reg_step == 3:
                        pwd = self.view.get_password("Tạo mật khẩu (hoặc '0' để LÙI LẠI sửa Số điện thoại): ")
                        if pwd == '0': 
                            reg_step = 2 
                        elif not pwd:
                            self.view.show_message("Mật khẩu không được để trống!", False)
                        else:
                            reg_step = 4 
                
                if cancel_registration:
                    continue 

                if reg_step == 4:
                    try:
                        cust_id = self.model.create_customer(name, username, phone, pwd)
                        logging.info(f"Tài khoản khách hàng mới được tạo: '{username}' (ID: {cust_id})")
                        self.view.show_message("Tạo tài khoản thành công!")
                        self.view.get_input("Nhấn Enter để tiếp tục vào Menu chính...")
                        return {"CustomerID": cust_id, "CustomerName": name, "Username": username}
                    except Exception as e:
                        logging.error(f"Lỗi tạo tài khoản: {e}")
                        self.view.show_message("Lỗi: Số điện thoại hoặc Tên đăng nhập này đã có người sử dụng!", False)
                        self.view.get_input("Nhấn Enter để thử lại...")
                        continue 

    def check_and_format_seat(self, seat_input, room_name):
        seat_input = seat_input.strip().upper()
        if len(seat_input) < 2: return None

        row_char = seat_input[0]
        try:
            col_num = int(seat_input[1:])
        except ValueError:
            return None
        return f"{row_char}{col_num:02d}"

    def _select_movie_and_date(self):
        step = 1
        selected_genre = selected_movie = selected_date = None

        while step > 0:
            self.view.clear_screen()
            if step == 1:
                genres = self.model.get_active_genres()
                self.view.display_list(genres, "BƯỚC 1: CHỌN THỂ LOẠI")
                idx = self.get_valid_idx(genres, "Nhập số chọn (0 để QUAY LẠI MENU): ")
                if idx == -1: return None, None
                selected_genre = genres[idx]
                step = 2
            elif step == 2:
                movies = self.model.get_movies_by_genre(selected_genre)
                self.view.display_list(movies, f"BƯỚC 2: PHIM THỂ LOẠI {selected_genre.upper()}")
                idx = self.get_valid_idx(movies, "Nhập số chọn (0 để QUAY LẠI): ")
                if idx == -1: step = 1
                else:
                    selected_movie = movies[idx]
                    step = 3
            elif step == 3:
                dates = self.model.get_dates_for_movie(selected_movie)
                self.view.display_list(dates, f"BƯỚC 3: CHỌN NGÀY CHIẾU CỦA '{selected_movie}'")
                idx = self.get_valid_idx(dates, "Nhập số chọn (0 để QUAY LẠI): ")
                if idx == -1: step = 2
                else:
                    selected_date = dates[idx]
                    return selected_movie, selected_date 

        return None, None

    def _process_booking(self, movie, date):
        step = 4
        selected_scr = None
        cust_id = self.current_user['CustomerID']

        while step >= 4:
            self.view.clear_screen()
            if step == 4:
                screenings = self.model.get_screenings_for_booking(movie, date)
                self.view.display_list(screenings, f"BƯỚC 4: CHỌN SUẤT CHIẾU ({date})")
                idx = self.get_valid_idx(screenings, "Nhập số chọn (0 để HỦY ĐẶT VÉ): ")
                if idx == -1: return 
                selected_scr = screenings[idx]
                step = 5
            elif step == 5:
                booked_seats, rows, cols = self.model.get_seat_layout_data(selected_scr['ScreeningID'])
                self.view.display_seat_map(booked_seats, selected_scr['RoomName'], rows, cols)
                
                seat_input = self.view.get_input("Nhập mã ghế (VD: A05, nhập '0' để CHỌN LẠI SUẤT): ")
                if seat_input.strip() == '0':
                    step = 4 
                else:
                    valid_seat = self.check_and_format_seat(seat_input, selected_scr['RoomName'])
                    if not valid_seat:
                        self.view.show_message("Định dạng ghế không hợp lệ (Bắt buộc 1 chữ + số)!", False)
                        self.view.get_input("\nNhấn Enter để chọn lại...")
                    elif valid_seat in booked_seats:
                        self.view.show_message("Ghế này đã có người đặt. Vui lòng chọn ghế trống [ ]!", False)
                        self.view.get_input("\nNhấn Enter để chọn lại...")
                    else:
                        try:
                            ticket_id = self.model.book_ticket(cust_id, selected_scr['ScreeningID'], valid_seat)
                            logging.info(f"Khách hàng '{self.current_user['Username']}' đã đặt thành công vé ID {ticket_id} (Ghế {valid_seat}, Suất ID {selected_scr['ScreeningID']}).")
                            self.view.show_message(f"ĐẶT VÉ THÀNH CÔNG!\nMã vé (TicketID): {ticket_id}\nPhim: {movie}\nNgày: {date} | Suất: {selected_scr['ScreeningTime']}\nGhế: {valid_seat}")
                            self.view.get_input("\nNhấn Enter để quay về Menu chính...")
                            return 
                        except Exception as e:
                            logging.error(f"Lỗi đặt vé: {e}")
                            self.view.show_message(str(e), False)
                            self.view.get_input("\nNhấn Enter để thử lại...")

    def handle_view_schedule(self, is_manager=False):
        self._unified_flow(is_manager=is_manager, start_as_view=True)

    def handle_online_booking(self):
        self._unified_flow(is_manager=False, start_as_view=False)

    def _unified_flow(self, is_manager=False, start_as_view=False):
        step = 1
        selected_genre = selected_movie = selected_date = selected_scr = None

        while step > 0:
            self.view.clear_screen()
            
            if step == 1:
                genres = self.model.get_active_genres()
                self.view.display_list(genres, "BƯỚC 1: CHỌN THỂ LOẠI")
                idx = self.get_valid_idx(genres, "Nhập số chọn (0 để QUAY LẠI MENU CHÍNH): ")
                if idx == -1: step = 0
                else:
                    selected_genre = genres[idx]
                    step = 2
                    
            elif step == 2:
                movies = self.model.get_movies_by_genre(selected_genre)
                self.view.display_list(movies, f"BƯỚC 2: PHIM THỂ LOẠI {selected_genre.upper()}")
                idx = self.get_valid_idx(movies, "Nhập số chọn (0 để QUAY LẠI CHỌN THỂ LOẠI): ")
                if idx == -1: step = 1
                else:
                    selected_movie = movies[idx]
                    step = 3
                    
            elif step == 3:
                dates = self.model.get_dates_for_movie(selected_movie)
                self.view.display_list(dates, f"BƯỚC 3: CHỌN NGÀY CHIẾU CỦA '{selected_movie}'")
                idx = self.get_valid_idx(dates, "Nhập số chọn (0 để QUAY LẠI CHỌN PHIM): ")
                if idx == -1: step = 2
                else:
                    selected_date = dates[idx]
                    step = 4 if start_as_view else 5

            elif step == 4:
                df = self.model.get_schedule_by_movie_and_date(selected_movie, selected_date)
                self.view.show_table(df, f"LỊCH CHIẾU: {selected_movie} ({selected_date})")
                
                print("\n" + "═"*45)
                if not is_manager:
                    print("  1. 🎫 Đặt vé cho phim này ngay")
                print("  0. 🔙 Quay lại chọn Ngày chiếu")
                print("  9. 🏠 Thoát về Menu chính")
                print("═"*45)
                
                choice = self._get_menu_choice("Bạn muốn làm gì tiếp theo?: ")
                
                if choice == '1' and not is_manager:
                    step = 5 
                elif choice == '0':
                    step = 3 
                elif choice == '9':
                    step = 0 
                else:
                    self.view.show_message("Lựa chọn không hợp lệ.", False)
                    self.view.get_input("\nNhấn Enter để thử lại...")

            elif step == 5:
                screenings = self.model.get_screenings_for_booking(selected_movie, selected_date)
                self.view.display_list(screenings, f"BƯỚC 4: CHỌN SUẤT CHIẾU ({selected_date})")
                
                idx = self.get_valid_idx(screenings, "Nhập số chọn (0 để QUAY LẠI): ")
                if idx == -1: 
                    step = 4 if start_as_view else 3
                else:
                    selected_scr = screenings[idx]
                    step = 6

            elif step == 6:
                booked_seats, rows, cols = self.model.get_seat_layout_data(selected_scr['ScreeningID'])
                self.view.display_seat_map(booked_seats, selected_scr['RoomName'], rows, cols)
                
                seat_input = self.view.get_input("Nhập mã ghế (VD: A05, nhập '0' để CHỌN LẠI SUẤT): ")
                if seat_input.strip() == '0':
                    step = 5 
                else:
                    valid_seat = self.check_and_format_seat(seat_input, selected_scr['RoomName'])
                    if not valid_seat:
                        self.view.show_message("Định dạng ghế không hợp lệ (Bắt buộc 1 chữ + số)!", False)
                        self.view.get_input("\nNhấn Enter để chọn lại...")
                    elif valid_seat in booked_seats:
                        self.view.show_message("Ghế này đã có người đặt. Vui lòng chọn ghế trống [ ]!", False)
                        self.view.get_input("\nNhấn Enter để chọn lại...")
                    else:
                        try:
                            cust_id = self.current_user['CustomerID']
                            ticket_id = self.model.book_ticket(cust_id, selected_scr['ScreeningID'], valid_seat)
                            logging.info(f"Khách hàng '{self.current_user['Username']}' đã đặt thành công vé ID {ticket_id} (Ghế {valid_seat}, Suất ID {selected_scr['ScreeningID']}).")
                            self.view.show_message(f"ĐẶT VÉ THÀNH CÔNG!\nMã vé (TicketID): {ticket_id}\nPhim: {selected_movie}\nNgày: {selected_date} | Suất: {selected_scr['ScreeningTime']}\nGhế: {valid_seat}")
                            self.view.get_input("\nNhấn Enter để quay về Menu chính...")
                            step = 0 
                        except Exception as e:
                            logging.error(f"Lỗi đặt vé: {e}")
                            self.view.show_message(str(e), False)
                            self.view.get_input("\nNhấn Enter để thử lại...")

    def handle_cancel_ticket(self):
        import pandas as pd # Import pandas để xử lý thời gian chính xác
        self.view.clear_screen()
        print("\n--- 🔍 TRA CỨU & HỦY VÉ ---")
        
        cust_id = self.current_user['CustomerID']

        while True:
            tickets = self.model.get_tickets_by_customer(cust_id)
            self.view.clear_screen()
            
            if not tickets:
                self.view.show_message("Bạn chưa đặt bất kỳ vé nào.", False)
                break 
            
            print(f"\nDANH SÁCH VÉ CỦA: {self.current_user['CustomerName'].upper()}")
            print("-" * 105)
            # In ra danh sách có cột Trạng thái và Thời gian mua rất xịn xò
            for i, t in enumerate(tickets, 1):
                status_icon = "🟢 Đã đặt" if t['TicketStatus'] == 'Booked' else "🔴 Đã hủy"
                print(f" {i:02d}. [Vé {t['TicketID']}] {t['MovieTitle'][:25]:<25} | {t['ScreeningDate']} {t['ScreeningTime']} | Ghế: {t['SeatNumber']:<4} | Mua lúc: {t['BookingTime']} | {status_icon}")
            print("-" * 105)
            
            idx = self.get_valid_idx(tickets, "Chọn số thứ tự vé muốn hủy (0 để thoát): ")
            
            if idx == -1: 
                break 
            
            selected_ticket = tickets[idx]
            t_id = selected_ticket['TicketID']
            
            # BẢO VỆ 1: Vé đã hủy thì không cho hủy lại
            if selected_ticket['TicketStatus'] == 'Cancelled':
                self.view.show_message(f"LỖI: Vé số {t_id} đã bị hủy từ trước, không thể thao tác lại!", False)
                self.view.get_input("\nNhấn Enter để chọn lại...")
                continue
            
            # =========================================================
            # 🛡️ BẢO VỆ DOANH THU: CHẶN HỦY VÉ QUÁ HẠN (CUT-OFF TIME)
            # =========================================================
            showtime = pd.to_datetime(selected_ticket['ScreeningDate']) + pd.to_timedelta(selected_ticket['ScreeningTime'])
            now = pd.Timestamp.now()
            time_diff = showtime - now
            
            if time_diff.total_seconds() < 0:
                self.view.show_message(f"TỪ CHỐI: Suất chiếu này đã diễn ra vào lúc {selected_ticket['ScreeningTime']}, bạn không thể hủy vé!", False)
                self.view.get_input("\nNhấn Enter để chọn lại...")
                continue
            elif time_diff.total_seconds() < 900: # 900 giây = đúng 15 phút
                self.view.show_message("TỪ CHỐI: Rạp đã khóa sổ. Chính sách chỉ cho phép hủy vé trước giờ chiếu tối thiểu 15 phút!", False)
                self.view.get_input("\nNhấn Enter để chọn lại...")
                continue
            # =========================================================
            
            confirm = self.view.get_input(f"Xác nhận hủy vé mã {t_id}? (y/n): ")
            
            if confirm.lower() == 'y':
                if self.model.cancel_ticket(t_id):
                    logging.info(f"Khách hàng '{self.current_user['Username']}' đã hủy thành công vé ID {t_id}.")
                    self.view.show_message(f"Đã hủy vé mã {t_id} thành công! (Tiền sẽ được hoàn lại sau 3 ngày)")
                else:
                    logging.error(f"Có lỗi xảy ra khi hủy vé ID {t_id} cho khách hàng '{self.current_user['Username']}'")
                    self.view.show_message("Có lỗi xảy ra khi hủy vé.", False)
                self.view.get_input("\nNhấn Enter để tiếp tục...")

        self.view.get_input("\nNhấn Enter để về Menu chính...")

    def handle_revenue_report(self):
        while True:
            self.view.clear_screen()
            print("\n" + "═"*75)
            print("📊 BÁO CÁO DOANH THU TỔNG QUAN THEO THÁNG".center(75))
            print("═"*75)
            
            summary_df = self.model.get_monthly_revenue_summary()
            if summary_df.empty:
                self.view.show_message("Chưa có dữ liệu bán vé nào.", False)
                break

            self.view.show_table(summary_df, "TỔNG QUAN DOANH THU TOÀN HỆ THỐNG")

            months = summary_df['Tháng'].tolist()
            
            print("\n" + "═"*75)
            print("📋 DANH SÁCH THÁNG ĐỂ XEM CHI TIẾT:")
            for i, month in enumerate(months, 1):
                print(f"  {i}. Xem chi tiết hiệu suất phim trong tháng {month}")
            print("  0. 🔙 Quay lại Menu Quản lý")
            print("═"*75)
            
            choice = self._get_menu_choice("Chọn số thứ tự tháng (hoặc 0 để thoát): ")
            
            try:
                idx = int(choice)
                if idx == 0:
                    break
                elif 1 <= idx <= len(months):
                    selected_month = months[idx - 1]
                    self.view.clear_screen()
                    detail_df = self.model.get_movie_details_by_month(selected_month)
                    
                    print("\n" + "═"*85)
                    print(f"🎬 CHI TIẾT HIỆU SUẤT PHIM - THÁNG {selected_month}".center(85))
                    print("═"*85)
                    
                    self.view.show_table(detail_df, "")
                    self.view.get_input("\nNhấn Enter để quay lại báo cáo tổng quan...")
                else:
                    self.view.show_message("Lựa chọn nằm ngoài danh sách!", False)
                    self.view.get_input("\nNhấn Enter để thử lại...")
            except ValueError:
                self.view.show_message("Vui lòng nhập số hợp lệ!", False)
                self.view.get_input("\nNhấn Enter để thử lại...")
        
    # ==========================================
    # LUỒNG QUẢN LÝ DỮ LIỆU (CRUD TỪ ADMIN)
    # ==========================================
    def handle_data_management(self, current_role):
        while True:
            self.view.clear_screen()
            print("\n" + "═"*55)
            print("🛠️ QUẢN LÝ HỆ THỐNG DỮ LIỆU".center(55))
            print("═"*55)
            print("  1. 🎬 Quản lý Danh mục Phim (Thêm/Sửa/Xóa)")
            print("  2. 🚪 Quản lý Phòng Chiếu & Sơ đồ ghế ") # <--- MENU MỚI THÊM
            print("  3. 📅 Xếp Lịch Chiếu Mới ")
            print("  4. 👥 Xem danh sách Khách hàng")
            print("  5. 🎫 Tra cứu Lịch sử Giao dịch (Vé) của Khách")
            print("  0. 🔙 Quay lại Bảng điều khiển chính")
            print("═"*55)
            
            choice = self._get_menu_choice("Chọn chức năng (0-5): ")
            
            if choice == '1':
                if current_role == 'Manager': self.handle_movie_management()
                else: self.view.show_message("TỪ CHỐI TRUY CẬP: Chỉ Quản lý rạp mới được thay đổi dữ liệu phim!", False); self.view.get_input("\nNhấn Enter để tiếp tục...")
            elif choice == '2': # Xử lý chức năng gọi phòng chiếu
                if current_role == 'Manager': self.handle_room_management()
                else: self.view.show_message("TỪ CHỐI TRUY CẬP!", False); self.view.get_input("\nNhấn Enter để tiếp tục...")
            elif choice == '3':
                if current_role == 'Manager': self.handle_screening_management()
                else: self.view.show_message("TỪ CHỐI TRUY CẬP!", False); self.view.get_input("\nNhấn Enter để tiếp tục...")
            elif choice == '4':
                self.handle_view_customers()
            elif choice == '5':
                self.handle_view_transactions()
            elif choice == '0':
                break
            else:
                self.view.show_message("Lựa chọn không hợp lệ.", False)
                self.view.get_input("\nNhấn Enter để thử lại...")
                
    def handle_room_management(self):
        """Giao diện Quản lý Phòng chiếu và Sơ đồ ghế"""
        while True:
            self.view.clear_screen()
            print("\n--- 🚪 QUẢN LÝ PHÒNG CHIẾU (CINEMA ROOMS) ---")
            
            # Lấy danh sách phòng hiện tại
            rooms = self.model.get_all_rooms()
            if rooms:
                print("\n📋 DANH SÁCH CÁC PHÒNG CHIẾU ĐANG VẬN HÀNH:")
                for r in rooms:
                    print(f" - [ID: {r['RoomID']:02d}] {r['RoomName']:<20} | Sức chứa: {r['Capacity']} ghế")
            
            print("\n" + "-"*65)
            print("  1. ➕ Khai báo thêm Phòng chiếu mới (Tự động sinh sơ đồ ghế)")
            print("  0. 🔙 Quay lại Menu Quản lý Dữ liệu")
            
            choice = self._get_menu_choice("\nBạn muốn làm gì?: ")
            
            if choice == '0':
                break
            elif choice == '1':
                print("\n--- KHAI BÁO PHÒNG CHIẾU MỚI ---")
                print("(💡 Gõ '0' ở bất kỳ bước nào để hủy)\n")
                
                # 1. Nhập Tên/Định dạng phòng
                room_types = ['Standard 2D', 'VIP', 'Couple', 'IMAX']
                self.view.display_list(room_types, "CHỌN ĐỊNH DẠNG PHÒNG")
                
                selected_type = None
                while True:
                    t_idx_str = self.view.get_input("Nhập số chọn định dạng phòng (0 để Hủy): ").strip()
                    if t_idx_str == '0': break
                    try:
                        t_idx = int(t_idx_str)
                        if 1 <= t_idx <= len(room_types):
                            selected_type = room_types[t_idx - 1]
                            break
                        else: self.view.show_message("Số không hợp lệ!", False)
                    except: self.view.show_message("Vui lòng nhập số!", False)
                if t_idx_str == '0': continue
                
                # Tạo tên phòng mẫu
                next_id = len(rooms) + 1 if rooms else 1
                default_name = f"Screen {next_id:03d} - {selected_type}"
                room_name = self.view.get_input(f"\nNhập tên phòng chiếu [{default_name}]: ").strip()
                if not room_name: room_name = default_name
                if room_name == '0': continue
                
                # 2. Nhập quy mô (Hàng x Cột)
                while True:
                    rows_str = self.view.get_input("\nNhập số lượng Hàng ghế (Từ 3 đến 15): ").strip()
                    if rows_str == '0': break
                    try:
                        rows = int(rows_str)
                        if 3 <= rows <= 15: break
                        else: self.view.show_message("Số hàng không hợp lý!", False)
                    except: self.view.show_message("Vui lòng nhập số nguyên!", False)
                if rows_str == '0': continue
                
                while True:
                    cols_str = self.view.get_input("Nhập số lượng Ghế mỗi hàng (Cột, Từ 5 đến 20): ").strip()
                    if cols_str == '0': break
                    try:
                        cols = int(cols_str)
                        if 5 <= cols <= 20: break
                        else: self.view.show_message("Số cột không hợp lý!", False)
                    except: self.view.show_message("Vui lòng nhập số nguyên!", False)
                if cols_str == '0': continue
                
                # 3. Tạo phòng
                print("\n⚙️ Đang xử lý tính toán sơ đồ ghế và lưu vào cơ sở dữ liệu...")
                success, msg = self.model.add_cinema_room_with_seats(room_name, selected_type, rows, cols)
                if success:
                    logging.info(f"ADMIN ACTION: Đã thêm phòng chiếu mới '{room_name}' ({rows} hàng x {cols} cột).")
                self.view.show_message(msg, success)
                self.view.get_input("\nNhấn Enter để tiếp tục...")            
                
    def handle_view_transactions(self):
        """Màn hình tra cứu lịch sử mua/hủy vé của Quản lý và Nhân viên"""
        while True:
            self.view.clear_screen()
            print("\n--- 🎫 TRA CỨU GIAO DỊCH VÉ ---")
            print("(💡 Mẹo: Vào mục '3. Xem danh sách Khách hàng' để lấy ID Khách)")
            
            cust_id_str = self.view.get_input("\nNhập ID Khách hàng cần tra cứu (hoặc 0 để thoát): ").strip()
            if cust_id_str == '0': break
            
            try:
                cust_id = int(cust_id_str)
                tickets = self.model.get_tickets_by_customer(cust_id)
                
                if not tickets:
                    self.view.show_message(f"Khách hàng mang ID {cust_id} chưa có giao dịch nào hoặc ID không tồn tại.", False)
                    self.view.get_input("\nNhấn Enter để thử lại...")
                    continue

                self.view.clear_screen()
                print(f"\n📋 LỊCH SỬ GIAO DỊCH CỦA KHÁCH HÀNG ID: {cust_id}")
                print("-" * 105)
                # In ra danh sách có đầy đủ thông tin để đối soát
                for i, t in enumerate(tickets, 1):
                    status_icon = "🟢 Đã đặt" if t['TicketStatus'] == 'Booked' else "🔴 Đã hủy"
                    print(f" {i:02d}. [Vé {t['TicketID']}] {t['MovieTitle'][:25]:<25} | {t['ScreeningDate']} {t['ScreeningTime']} | Ghế: {t['SeatNumber']:<4} | Mua/Hủy lúc: {t['BookingTime']} | {status_icon}")
                print("-" * 105)
                
                self.view.get_input("\nNhấn Enter để tra cứu khách hàng khác...")
                
            except ValueError:
                self.view.show_message("ID Khách hàng phải là chữ số!", False)
                self.view.get_input("\nNhấn Enter để thử lại...")            

    def handle_movie_management(self):
        while True:
            self.view.clear_screen()
            print("\n--- 🎬 QUẢN LÝ DANH MỤC PHIM ---")
            
            # Sử dụng hàm lấy phim kèm số vé đã bán
            movies = self.model.get_movies_with_ticket_counts()
            genres = self.model.get_active_genres() 
            
            if movies:
                print("\n📋 DANH SÁCH TẤT CẢ PHIM TRONG HỆ THỐNG:")
                print("(💡 BẢO VỆ DỮ LIỆU: Phim ĐÃ CÓ KHÁCH MUA VÉ sẽ BỊ KHÓA Sửa/Xóa)\n")
                
                for idx, m in enumerate(movies, 1):
                    # Hiển thị icon trạng thái
                    if m['TicketCount'] == 0:
                        status = "🟢 0 vé (Có thể Sửa/Xóa)"
                    else:
                        status = f"🔴 Đã bán {m['TicketCount']} vé (BỊ KHÓA)"
                        
                    print(f" {idx:02d}. [ID: {m['MovieID']:03d}] {m['MovieTitle'][:25]:<25} | Thể loại: {m['Genre'][:12]:<12} | {m['DurationMinutes']:>3} phút | {status}")
            
            print("\n" + "-"*80)
            print("  1. ➕ Thêm Phim Mới")
            print("  2. ✏️ Sửa Thông Tin Phim (Chỉ áp dụng phim 0 vé)")
            print("  3. 🗑️ Xóa Phim (Chỉ áp dụng phim 0 vé)")
            print("  0. 🔙 Quay lại Menu Quản lý Dữ liệu")
            
            choice = self._get_menu_choice("\nBạn muốn làm gì?: ")
            
            if choice == '0':
                break
            elif choice == '1': 
                print("\n--- NHẬP THÔNG TIN PHIM MỚI ---")
                print("(💡 Gõ '0' ở bất kỳ bước nào để hủy)")
                
                # 1. Nhập Tên Phim
                while True:
                    title = self.view.get_input("\nNhập tên phim: ").strip()
                    if title == '0': break
                    if not title:
                        self.view.show_message("Tên phim không được để trống!", False)
                        continue
                    break
                if title == '0': continue
                
                # 2. Chọn Thể Loại
                self.view.display_list(genres, "CHỌN THỂ LOẠI PHIM")
                genre = None
                while True:
                    g_idx_str = self.view.get_input("Nhập số thứ tự thể loại (hoặc '0' để hủy): ").strip()
                    if g_idx_str == '0': break
                    try:
                        g_idx = int(g_idx_str)
                        if 1 <= g_idx <= len(genres):
                            genre = genres[g_idx - 1]
                            break
                        else:
                            self.view.show_message("Số không nằm trong danh sách!", False)
                    except ValueError:
                        self.view.show_message("Vui lòng nhập số hợp lệ!", False)
                if g_idx_str == '0': continue

                # 3. Nhập Thời Lượng
                while True:
                    dur_str = self.view.get_input("\nNhập thời lượng (phút, VD: 120) hoặc '0' để hủy: ").strip()
                    if dur_str == '0': break
                    if not dur_str:
                        self.view.show_message("Thời lượng không được để trống!", False)
                        continue
                    try:
                        duration = int(dur_str)
                        if duration < 30 or duration > 300:
                            self.view.show_message("Thời lượng phim không hợp lý! Phải từ 30 đến 300 phút.", False)
                            continue
                        break
                    except ValueError:
                        self.view.show_message("Thời lượng phải là số nguyên dương!", False)
                if dur_str == '0': continue
                
                # Lưu DB
                self.model.add_movie(title, genre, duration)
                logging.info(f"ADMIN ACTION: Đã thêm phim mới '{title}' ({genre}, {duration} phút).")
                self.view.show_message(f"Đã thêm phim '{title}' thành công!")
                self.view.get_input("\nNhấn Enter để tiếp tục...")
                
            elif choice == '2': 
                if not movies: continue
                idx = self.get_valid_idx(movies, "\nNhập số thứ tự phim muốn SỬA (0 để Hủy): ")
                if idx == -1: continue
                
                selected = movies[idx]
                
                # 🛡️ BẢO VỆ CHẶN SỬA NẾU ĐÃ BÁN VÉ
                if selected['TicketCount'] > 0:
                    self.view.show_message(f"TỪ CHỐI: Phim '{selected['MovieTitle']}' đã bán {selected['TicketCount']} vé! Không thể sửa tên/thời lượng để tránh sai lệch thông tin vé đã bán cho khách.", False)
                    self.view.get_input("\nNhấn Enter để tiếp tục...")
                    continue
                
                print(f"\n--- ĐANG SỬA PHIM: {selected['MovieTitle']} ---")
                print("(💡 Nhấn Enter để giữ nguyên cũ, gõ '0' để hủy toàn bộ quá trình sửa)")
                
                # 1. Tên Phim
                while True:
                    new_title = self.view.get_input(f"\nTên phim mới [{selected['MovieTitle']}]: ").strip()
                    if new_title == '0': break
                    if not new_title:
                        new_title = selected['MovieTitle']
                    break
                if new_title == '0': continue
                
                # 2. Thể loại
                self.view.display_list(genres, "CHỌN THỂ LOẠI MỚI")
                new_genre = selected['Genre']
                while True:
                    g_idx_str = self.view.get_input(f"Chọn số thể loại mới [{selected['Genre']}]: ").strip()
                    if g_idx_str == '0': break
                    if not g_idx_str: break # Nhấn Enter giữ nguyên
                    try:
                        g_idx = int(g_idx_str)
                        if 1 <= g_idx <= len(genres):
                            new_genre = genres[g_idx - 1]
                            break
                        else:
                            self.view.show_message("Số không nằm trong danh sách!", False)
                    except ValueError:
                        self.view.show_message("Vui lòng nhập số hợp lệ!", False)
                if g_idx_str == '0': continue
                
                # 3. Thời Lượng
                while True:
                    new_dur_str = self.view.get_input(f"\nThời lượng mới [{selected['DurationMinutes']} phút]: ").strip()
                    if new_dur_str == '0': break
                    if not new_dur_str:
                        new_duration = selected['DurationMinutes']
                        break
                    try:
                        new_duration = int(new_dur_str)
                        if new_duration < 30 or new_duration > 300:
                            self.view.show_message("Thời lượng phim không hợp lý! Phải từ 30 đến 300 phút.", False)
                            continue
                        break
                    except ValueError:
                        self.view.show_message("Thời lượng phải là số!", False)
                if new_dur_str == '0': continue
                
                # Lưu DB
                self.model.update_movie(selected['MovieID'], new_title, new_genre, new_duration)
                logging.info(f"ADMIN ACTION: Đã cập nhật phim ID {selected['MovieID']} thành '{new_title}'.")
                self.view.show_message("Cập nhật thông tin phim thành công!")
                self.view.get_input("\nNhấn Enter để tiếp tục...")    
                    
            elif choice == '3': 
                if not movies: continue
                idx = self.get_valid_idx(movies, "\nNhập số thứ tự phim muốn XÓA (0 để Hủy): ")
                if idx == -1: continue
                
                selected = movies[idx]
                
                # 🛡️ BẢO VỆ CHẶN XÓA NẾU ĐÃ BÁN VÉ
                if selected['TicketCount'] > 0:
                    self.view.show_message(f"TỪ CHỐI: Phim '{selected['MovieTitle']}' đã bán được {selected['TicketCount']} vé! Xóa sẽ gây mất dữ liệu doanh thu.", False)
                    self.view.get_input("\nNhấn Enter để tiếp tục...")
                    continue

                confirm = self.view.get_input(f"⚠️ Bạn có chắc muốn xóa phim '{selected['MovieTitle']}'? (y/n): ")
                if confirm.lower() == 'y':
                    success, msg = self.model.delete_movie(selected['MovieID'])
                    if success:
                        logging.warning(f"ADMIN ACTION: Đã xóa phim '{selected['MovieTitle']}' (ID: {selected['MovieID']}) khỏi hệ thống.")
                    self.view.show_message(msg, success)
                self.view.get_input("\nNhấn Enter để tiếp tục...")
                
    def handle_screening_management(self):
        import pandas as pd
        while True:
            self.view.clear_screen()
            print("\n--- 📅 XẾP LỊCH CHIẾU MỚI ---")
            
            # 1. CHỌN PHIM
            movies = self.model.get_all_movies()
            if not movies:
                self.view.show_message("Chưa có phim nào. Hãy thêm phim trước!", False)
                self.view.get_input("\nNhấn Enter để quay lại...")
                break
                
            self.view.display_list([f"[ID: {m['MovieID']}] {m['MovieTitle']}" for m in movies], "1. CHỌN PHIM ĐỂ XẾP LỊCH")
            idx_m = self.get_valid_idx(movies, "Nhập số thứ tự phim (0 để Thoát): ")
            if idx_m == -1: break
            selected_movie = movies[idx_m]

            # 2. CHỌN PHÒNG
            rooms = self.model.get_all_rooms()
            self.view.display_list([f"{r['RoomName']} (Sức chứa: {r['Capacity']} ghế)" for r in rooms], "2. CHỌN PHÒNG CHIẾU (ĐỊNH DẠNG IMAX/3D/2D)")
            idx_r = self.get_valid_idx(rooms, "Nhập số thứ tự phòng (0 để Thoát): ")
            if idx_r == -1: continue # Lùi lại chọn phim
            selected_room = rooms[idx_r]

            # 3. NHẬP NGÀY VÀ GIỜ (Có tính năng Giữ trạng thái)
            cancel_scheduling = False
            while True: # VÒNG LẶP NHẬP NGÀY
                print("\n--- 3. THIẾT LẬP THỜI GIAN ---")
                date_str = self.view.get_input("Nhập ngày chiếu (YYYY-MM-DD) hoặc '0' để HỦY XẾP LỊCH: ").strip()
                if date_str == '0':
                    cancel_scheduling = True
                    break # Thoát vòng lặp Ngày -> Bay hẳn ra ngoài

                # Validate định dạng Ngày
                try:
                    pd.to_datetime(date_str, format='%Y-%m-%d')
                except ValueError:
                    self.view.show_message("Định dạng Ngày không hợp lệ! Vui lòng nhập đúng YYYY-MM-DD.", False)
                    continue # Bắt nhập lại Ngày ngay lập tức

                back_to_date = False
                success_schedule = False
                
                while True: # VÒNG LẶP NHẬP GIỜ
                    time_str = self.view.get_input("Nhập giờ chiếu (HH:MM) hoặc '0' để SỬA LẠI NGÀY: ").strip()
                    if time_str == '0':
                        back_to_date = True
                        break # Thoát vòng lặp Giờ -> Quay lại vòng lặp Ngày

                    # Validate định dạng Giờ
                    try:
                        pd.to_datetime(time_str, format='%H:%M')
                    except ValueError:
                        self.view.show_message("Định dạng Giờ không hợp lệ! Vui lòng nhập đúng HH:MM.", False)
                        continue # Bắt nhập lại Giờ ngay lập tức
                    
                    # 🔴 BẢO VỆ LỚP 1: Chặn đặt lịch trong quá khứ
                    schedule_datetime = pd.to_datetime(f"{date_str} {time_str}")
                    if schedule_datetime < pd.Timestamp.now():
                        self.view.show_message("LỖI: Không thể xếp lịch cho thời điểm trong quá khứ! Hãy nhập giờ/ngày khác.", False)
                        continue # Bắt nhập lại Giờ (có thể bấm 0 để lùi ra sửa ngày nếu muốn)
                    
                    # 🔴 BẢO VỆ LỚP 2: Chặn trùng lịch & Ép thời gian dọn rạp
                    is_conflict, conflict_msg = self.model.check_schedule_conflict(
                        selected_room['RoomID'], 
                        date_str, 
                        time_str, 
                        selected_movie['DurationMinutes']
                    )
                    
                    if is_conflict:
                        self.view.show_message(f"XUNG ĐỘT LỊCH CHIẾU!\n👉 {conflict_msg}", False)
                        continue # Bắt nhập lại Giờ khác ngay lập tức

                    # Thành công! Lưu DB
                    time_formatted = f"{time_str}:00" 
                    self.model.add_screening(selected_movie['MovieID'], selected_room['RoomID'], date_str, time_formatted)
                    logging.info(f"ADMIN ACTION: Đã xếp lịch chiếu phim '{selected_movie['MovieTitle']}' tại phòng '{selected_room['RoomName']}' lúc {time_str} ngày {date_str}.")
                    self.view.show_message(f"Đã xếp lịch chiếu thành công!\n👉 Phim: {selected_movie['MovieTitle']}\n👉 Phòng: {selected_room['RoomName']}\n👉 Lúc: {time_str} ngày {date_str}")
                    self.view.get_input("\nNhấn Enter để tiếp tục...")
                    
                    success_schedule = True
                    break # Thoát vòng lặp Giờ
                
                # Xử lý luồng sau khi thoát vòng lặp Giờ
                if success_schedule:
                    cancel_scheduling = True # Đã xong 1 phim, bay thẳng ra bảng chọn phim mới
                    break
                if back_to_date:
                    continue # Bắt đầu lại vòng lặp Ngày

            # Xử lý luồng thoát ra ngoài cùng
            if cancel_scheduling:
                break # Phá vỡ vòng lặp Main -> Trở về Menu Dữ Liệu
     
    def handle_view_customers(self):
        """Màn hình xem danh sách khách hàng dành cho Staff"""
        self.view.clear_screen()
        print("\n" + "═"*75)
        print("👥 DANH SÁCH KHÁCH HÀNG THÂN THIẾT".center(75))
        print("═"*75)
        
        df = self.model.get_all_customers_summary()
        if df.empty:
            self.view.show_message("Chưa có khách hàng nào trong hệ thống.", False)
        else:
            # Masking số điện thoại để tăng tính bảo mật (Chỉ hiện 3 số đầu và 3 số cuối)
            df['Số Điện Thoại'] = df['Số Điện Thoại'].apply(lambda x: f"{x[:3]}****{x[-3:]}" if len(x) > 6 else x)
            self.view.show_table(df, "")
            print("\n💡 Ghi chú: Vì lý do bảo mật, nhân viên không được quyền chỉnh sửa thông tin khách hàng.")
            
        self.view.get_input("\nNhấn Enter để quay lại...")