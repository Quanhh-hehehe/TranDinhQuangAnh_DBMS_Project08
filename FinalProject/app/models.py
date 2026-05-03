import pandas as pd
import bcrypt
import logging
from .database_helper import DatabaseHelper

class CinemaModel:
    def __init__(self):
        try:
            self.conn = DatabaseHelper.get_connection()
            self.cursor = self.conn.cursor()
            logging.info("Kết nối Database trong Models thành công.")
        except Exception as e:
            logging.critical(f"Lỗi kết nối MySQL nghiêm trọng: {e}")
            print(f"Lỗi kết nối MySQL: {e}")

    def _format_time_range(self, df):
        if df.empty: return df
        df_formatted = df.copy()
        duration_td = pd.to_timedelta(df_formatted['DurationMinutes'], unit='m')
        end_time_td = df_formatted['ScreeningTime'] + duration_td
        def format_hhmm(td):
            comp = td.components
            return f"{(comp.hours % 24):02d}:{comp.minutes:02d}"
        df_formatted['ScreeningTime'] = df_formatted['ScreeningTime'].apply(format_hhmm) + " - " + end_time_td.apply(format_hhmm)
        if 'Genre' in df_formatted.columns: df_formatted = df_formatted.drop(columns=['Genre'])
        return df_formatted

    # --- TRUY VẤN LỊCH CHIẾU ---
    def get_active_genres(self):
        query = "SELECT GenreName FROM Genres ORDER BY GenreName"
        df = pd.read_sql(query, self.conn)
        return df['GenreName'].tolist() if not df.empty else []

    def get_movies_by_genre(self, genre):
        query = "SELECT DISTINCT MovieTitle FROM v_ScreeningSchedule WHERE Genre LIKE %s ORDER BY MovieTitle"
        search_pattern = f"%{genre}%"
        df = pd.read_sql(query, self.conn, params=[search_pattern])
        return df['MovieTitle'].tolist() if not df.empty else []

    def get_dates_for_movie(self, movie_title):
        query = "SELECT DISTINCT ScreeningDate FROM v_ScreeningSchedule WHERE MovieTitle = %s ORDER BY ScreeningDate"
        df = pd.read_sql(query, self.conn, params=[movie_title])
        return df['ScreeningDate'].astype(str).tolist() if not df.empty else []

    def get_schedule_by_movie_and_date(self, movie_title, screening_date):
        query = "SELECT * FROM v_ScreeningSchedule WHERE MovieTitle = %s AND ScreeningDate = %s ORDER BY ScreeningTime"
        df = pd.read_sql(query, self.conn, params=[movie_title, screening_date])
        return self._format_time_range(df)

    # --- QUẢN LÝ TÀI KHOẢN (KHÁCH HÀNG VÀ NHÂN VIÊN) ---
    def get_customer_by_username(self, username):
        """Lấy thông tin khách hàng bằng Username"""
        query = "SELECT CustomerID, CustomerName, Password FROM Customers WHERE Username = %s LIMIT 1"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        return {"CustomerID": result[0], "CustomerName": result[1], "Password": result[2]} if result else None

    def get_staff_by_username(self, username):
        """Lấy thông tin Quản lý/Nhân viên bằng Username"""
        query = "SELECT StaffID, FullName, Password, Role FROM Staff WHERE Username = %s LIMIT 1"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        return {"StaffID": result[0], "FullName": result[1], "Password": result[2], "Role": result[3]} if result else None

    def verify_password(self, plain_password, hashed_password):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
            return plain_password == hashed_password

    def create_customer(self, name, username, phone, password):
        """Tạo tài khoản: Yêu cầu cả Username và Phone"""
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        self.cursor.execute("SELECT MAX(CustomerID) FROM Customers")
        new_id = (self.cursor.fetchone()[0] or 0) + 1
        
        query = "INSERT INTO Customers (CustomerID, CustomerName, Username, PhoneNumber, Password) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(query, (new_id, name, username, phone, hashed_password))
        self.conn.commit()
        return new_id

    # --- ĐẶT VÉ VÀ TRA CỨU VÉ ---
    def get_screenings_for_booking(self, movie_title, screening_date):
        query = "SELECT ScreeningID, ScreeningTime, RoomName, DurationMinutes FROM v_ScreeningSchedule WHERE MovieTitle = %s AND ScreeningDate = %s"
        df = pd.read_sql(query, self.conn, params=[movie_title, screening_date])
        
        if not df.empty:
            # =========================================================
            # 🛡️ BẢO VỆ VẬN HÀNH: GIỜ KHÓA SỔ ĐẶT VÉ (CUT-OFF TIME)
            # =========================================================
            now = pd.Timestamp.now()
            # Ghép Ngày và Giờ thành 1 mốc thời gian hoàn chỉnh
            screening_datetime = pd.to_datetime(screening_date) + pd.to_timedelta(df['ScreeningTime'])
            
            # Lọc DataFrame: Chỉ giữ lại những suất chiếu còn cách hiện tại ÍT NHẤT 15 phút (Khóa sổ trước 15p)
            df = df[screening_datetime > (now + pd.Timedelta(minutes=15))]
            # =========================================================

        return self._format_time_range(df).to_dict('records')

    def get_seat_layout_data(self, screening_id):
        """Lấy danh sách ghế đã đặt VÀ kích thước thật của phòng chiếu"""
        # 1. Lấy danh sách ghế đã đặt
        query_booked = "SELECT SeatNumber FROM Tickets WHERE ScreeningID = %s AND TicketStatus = 'Booked'"
        df_booked = pd.read_sql(query_booked, self.conn, params=[screening_id])
        booked_seats = df_booked['SeatNumber'].tolist() if not df_booked.empty else []
        
        # 2. Lấy kích thước thật của phòng bằng cách quét bảng Seats
        query_size = """
            SELECT MAX(SUBSTRING(s.SeatNumber, 1, 1)) as MaxRow, 
                   MAX(CAST(SUBSTRING(s.SeatNumber, 2) AS UNSIGNED)) as MaxCol
            FROM Seats s
            JOIN Screenings scr ON s.RoomID = scr.RoomID
            WHERE scr.ScreeningID = %s
        """
        self.cursor.execute(query_size, (screening_id,))
        result = self.cursor.fetchone()
        
        if result and result[0] and result[1]:
            # Chuyển đổi chữ cái thành số thứ tự (A -> 1, B -> 2, O -> 15...)
            rows = ord(result[0].upper()) - 64 
            cols = int(result[1])
        else:
            rows, cols = 5, 8 # Kích thước dự phòng nếu phòng lỗi
            
        return booked_seats, rows, cols

    def book_ticket(self, cust_id, screen_id, seat_num):
        try:
            self.cursor.callproc('sp_BookTicket', (cust_id, screen_id, seat_num))
            self.conn.commit()

            self.cursor.execute("SELECT MAX(TicketID) FROM Tickets WHERE CustomerID = %s", (cust_id,))
            ticket_id = self.cursor.fetchone()[0]

            logging.info(f"Khách hàng ID {cust_id} vừa đặt thành công Vé ID {ticket_id} (Suất {screen_id}, Ghế {seat_num})")
            return ticket_id
        except Exception as e:
            self.conn.rollback()
            logging.warning(f"Lỗi khi Khách hàng {cust_id} đặt vé (Suất {screen_id}): {e}")
            raise e

    def get_tickets_by_customer(self, customer_id):
        query = """
            SELECT 
                t.TicketID, 
                m.MovieTitle, 
                s.ScreeningDate, 
                s.ScreeningTime, 
                t.SeatNumber,
                t.BookingTime,      -- BỔ SUNG: Lấy thời gian đặt
                t.TicketStatus      -- BỔ SUNG: Lấy trạng thái vé
            FROM Tickets t
            JOIN Screenings s ON t.ScreeningID = s.ScreeningID
            JOIN Movies m ON s.MovieID = m.MovieID
            WHERE t.CustomerID = %s
            ORDER BY t.TicketID DESC
        """
        df = pd.read_sql(query, self.conn, params=[customer_id])
        return df.to_dict('records') if not df.empty else []

    def cancel_ticket(self, ticket_id):
        # ĐỔI LỆNH DELETE THÀNH LỆNH UPDATE TRẠNG THÁI
        query = "UPDATE Tickets SET TicketStatus = 'Cancelled' WHERE TicketID = %s"
        self.cursor.execute(query, (ticket_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    # =======================================================
    # BÁO CÁO TỔNG QUAN & CHI TIẾT (DRILL-DOWN REPORTING)
    # =======================================================
    
    def get_monthly_revenue_summary(self):
        """Báo cáo 1: Lấy tổng quan doanh thu nhóm theo từng tháng"""
        query = """
            SELECT 
                DATE_FORMAT(o.ScreeningDate, '%m/%Y') AS 'Tháng',
                COUNT(o.ScreeningID) AS 'Số Suất Chiếu',
                SUM(o.TicketsSold) AS 'Tổng Vé Bán',
                SUM(fn_GetScreeningRevenue(o.ScreeningID)) AS 'Doanh Thu (VND)'
            FROM v_OccupancyReport o
            WHERE o.TicketsSold > 0 
            GROUP BY DATE_FORMAT(o.ScreeningDate, '%m/%Y')
            ORDER BY MAX(o.ScreeningDate) DESC
        """
        df = pd.read_sql(query, self.conn)
        if not df.empty:
            # Format tiền tệ để hiển thị đẹp trên View
            df['Doanh Thu (VND)'] = df['Doanh Thu (VND)'].apply(lambda x: f"{x:,.0f} ₫")
        return df

    def get_movie_details_by_month(self, month_str):
        """Báo cáo 2: Chi tiết phim + ĐỊNH DẠNG + NGÀY CHIẾU (Sắp xếp tăng dần theo thời gian)"""
        query = """
            SELECT 
                o.MovieTitle AS 'Tên Phim',
                o.RoomName AS 'Định Dạng (Phòng)',
                o.ScreeningDate AS 'Ngày Chiếu',
                SUM(o.TicketsSold) AS 'Tổng Vé',
                ROUND(AVG(o.OccupancyRate_Pct), 2) AS 'Lấp Đầy TB (%)',
                SUM(fn_GetScreeningRevenue(o.ScreeningID)) AS 'Doanh Thu (VND)'
            FROM v_OccupancyReport o
            WHERE DATE_FORMAT(o.ScreeningDate, '%m/%Y') = %s AND o.TicketsSold > 0
            GROUP BY o.MovieTitle, o.RoomName, o.ScreeningDate
            ORDER BY o.ScreeningDate ASC, SUM(o.TicketsSold) DESC
        """
        df = pd.read_sql(query, self.conn, params=[month_str])
        
        if not df.empty:
            total_tickets = df['Tổng Vé'].sum()
            total_rev = df['Doanh Thu (VND)'].sum()
            
            # Format tiền tệ
            df['Doanh Thu (VND)'] = df['Doanh Thu (VND)'].apply(lambda x: f"{x:,.0f} ₫")
            
            # Thêm dòng chốt sổ (Bảng giờ tăng lên 6 cột nên cần thêm một dấu '-' nữa)
            df.loc[len(df)] = [f'=== TỔNG CHI TIẾT {month_str} ===', '-', '-', total_tickets, '-', f"{total_rev:,.0f} ₫"]
            
        return df
    
    # =======================================================
    # QUẢN LÝ DỮ LIỆU (CRUD) - DÀNH CHO ADMIN
    # =======================================================
    def get_all_movies(self):
        """Lấy danh sách TOÀN BỘ phim trong hệ thống để Quản lý chọn sửa"""
        query = "SELECT MovieID, MovieTitle, Genre, DurationMinutes FROM Movies ORDER BY MovieID DESC"
        df = pd.read_sql(query, self.conn)
        return df.to_dict('records') if not df.empty else []

    def add_movie(self, title, genre, duration):
        """Thêm một bộ phim mới vào kho"""
        query = "INSERT INTO Movies (MovieTitle, Genre, DurationMinutes) VALUES (%s, %s, %s)"
        self.cursor.execute(query, (title, genre, duration))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_movie(self, movie_id, title, genre, duration):
        """Cập nhật thông tin phim khi bị nhập sai"""
        query = "UPDATE Movies SET MovieTitle = %s, Genre = %s, DurationMinutes = %s WHERE MovieID = %s"
        self.cursor.execute(query, (title, genre, duration, movie_id))
        self.conn.commit()
        return self.cursor.rowcount > 0
    # === BỔ SUNG VÀO PHẦN QUẢN LÝ DỮ LIỆU CỦA ADMIN ===
    def get_movies_with_ticket_counts(self):
        """Lấy danh sách phim kèm số lượng vé đã bán, sắp xếp tăng dần để quản lý dễ xóa phim 0 vé"""
        query = """
            SELECT 
                m.MovieID, 
                m.MovieTitle, 
                m.Genre, 
                m.DurationMinutes, 
                COUNT(t.TicketID) as TicketCount
            FROM Movies m
            LEFT JOIN Screenings s ON m.MovieID = s.MovieID
            LEFT JOIN Tickets t ON s.ScreeningID = t.ScreeningID
            GROUP BY m.MovieID, m.MovieTitle, m.Genre, m.DurationMinutes
            ORDER BY TicketCount ASC, m.MovieID DESC
        """
        import pandas as pd
        df = pd.read_sql(query, self.conn)
        return df.to_dict('records') if not df.empty else []
    
    def delete_movie(self, movie_id):
        """Xóa phim AN TOÀN: Chỉ cho xóa nếu chưa bán được vé nào"""
        check_query = """
            SELECT COUNT(t.TicketID) FROM Tickets t
            JOIN Screenings s ON t.ScreeningID = s.ScreeningID
            WHERE s.MovieID = %s
        """
        self.cursor.execute(check_query, (movie_id,))
        if self.cursor.fetchone()[0] > 0:
            return False, "❌ KHÔNG THỂ XÓA: Phim này đã có khách đặt vé! Xóa sẽ làm mất dữ liệu doanh thu."
        
        # Nếu = 0 vé, cho phép xóa. (Lịch chiếu trống của phim này sẽ tự bốc hơi nhờ ON DELETE CASCADE)
        del_query = "DELETE FROM Movies WHERE MovieID = %s"
        self.cursor.execute(del_query, (movie_id,))
        self.conn.commit()
        return True, "✅ Đã xóa phim thành công!"

    # --- CÁC HÀM PHỤC VỤ XẾP LỊCH CHIẾU MỚI ---
    def get_all_rooms(self):
        """Lấy danh sách tất cả phòng chiếu (Chứa định dạng IMAX, Couple, 2D)"""
        query = "SELECT RoomID, RoomName, Capacity FROM CinemaRooms ORDER BY RoomName"
        df = pd.read_sql(query, self.conn)
        return df.to_dict('records') if not df.empty else []

    def calculate_base_price(self, date_obj):
        """AI tự động tính giá vé cơ sở dựa trên ngày chiếu (Cuối tuần / Lễ)"""
        holidays = ['01-01', '02-14', '03-08', '04-30', '05-01', '09-02', '10-20', '12-24', '12-25', '12-31']
        month_day = date_obj.strftime('%m-%d')
        if month_day in holidays: return 50000.0
        if date_obj.weekday() >= 4: return 80000.0 # Thứ 6, 7, CN
        return 60000.0

    def add_screening(self, movie_id, room_id, date_str, time_str):
        """Thêm lịch chiếu mới và tự động tính Base Price"""
        date_obj = pd.to_datetime(date_str).date()
        base_price = self.calculate_base_price(date_obj)
        
        query = "INSERT INTO Screenings (MovieID, RoomID, ScreeningDate, ScreeningTime, BasePrice) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(query, (movie_id, room_id, date_str, time_str, base_price))
        self.conn.commit()
        return True
    def check_schedule_conflict(self, room_id, date_str, time_str, duration_minutes, exclude_screening_id=None):
        """Kiểm tra xung đột lịch (hỗ trợ loại trừ chính nó khi đang Edit)"""
        query = """
            SELECT m.MovieTitle, s.ScreeningTime, m.DurationMinutes
            FROM Screenings s
            JOIN Movies m ON s.MovieID = m.MovieID
            WHERE s.RoomID = %s AND s.ScreeningDate = %s
              AND CAST(%s AS TIME) < ADDTIME(s.ScreeningTime, SEC_TO_TIME((m.DurationMinutes + 15) * 60))
              AND ADDTIME(CAST(%s AS TIME), SEC_TO_TIME((%s + 15) * 60)) > s.ScreeningTime
        """
        time_formatted = f"{time_str}:00" if len(time_str) == 5 else time_str
        params = [room_id, date_str, time_formatted, time_formatted, duration_minutes]
        
        # Thêm điều kiện loại trừ chính suất chiếu này khi Sửa
        if exclude_screening_id:
            query += " AND s.ScreeningID != %s"
            params.append(exclude_screening_id)
            
        self.cursor.execute(query, tuple(params))
        conflict = self.cursor.fetchone()
        
        if conflict:
            movie_title = conflict[0]
            scr_time = conflict[1] 
            hours, remainder = divmod(scr_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            msg = f"Phòng này đang kẹt lịch phim '{movie_title}' lúc {hours:02d}:{minutes:02d}."
            return True, msg
        return False, ""
    
    # --- QUẢN LÝ THÔNG TIN KHÁCH HÀNG ---
    def update_customer_profile(self, cust_id, name, phone, password=None):
        """Khách hàng tự cập nhật thông tin cá nhân"""
        if password:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            query = "UPDATE Customers SET CustomerName = %s, PhoneNumber = %s, Password = %s WHERE CustomerID = %s"
            self.cursor.execute(query, (name, phone, hashed, cust_id))
        else:
            query = "UPDATE Customers SET CustomerName = %s, PhoneNumber = %s WHERE CustomerID = %s"
            self.cursor.execute(query, (name, phone, cust_id))
        self.conn.commit()
        return True

    def get_all_customers_summary(self):
        """Admin xem danh sách khách hàng (Không lấy Password để bảo mật)"""
        query = """
            SELECT 
                c.CustomerID AS 'ID',
                c.CustomerName AS 'Họ Tên',
                c.Username AS 'Tên Đăng Nhập',
                c.PhoneNumber AS 'Số Điện Thoại',
                COUNT(t.TicketID) AS 'Tổng Vé Đã Mua'
            FROM Customers c
            LEFT JOIN Tickets t ON c.CustomerID = t.CustomerID
            GROUP BY c.CustomerID
            ORDER BY COUNT(t.TicketID) DESC
        """
        df = pd.read_sql(query, self.conn)
        return df
    
    # === CÁC HÀM QUẢN LÝ SUẤT CHIẾU (SỬA/XÓA) ===
    def get_all_screenings_with_ticket_counts(self):
        """Lấy danh sách TẤT CẢ suất chiếu trong tương lai kèm số vé đã bán"""
        query = """
            SELECT 
                s.ScreeningID, m.MovieID, m.MovieTitle, m.DurationMinutes,
                c.RoomID, c.RoomName, s.ScreeningDate, s.ScreeningTime,
                (SELECT COUNT(*) FROM Tickets t WHERE t.ScreeningID = s.ScreeningID AND t.TicketStatus = 'Booked') as TicketCount
            FROM Screenings s
            JOIN Movies m ON s.MovieID = m.MovieID
            JOIN CinemaRooms c ON s.RoomID = c.RoomID
            WHERE TIMESTAMP(s.ScreeningDate, s.ScreeningTime) >= NOW() -- CHỈ LẤY TƯƠNG LAI
            ORDER BY s.ScreeningDate ASC, s.ScreeningTime ASC -- SẮP XẾP TỪ GẦN ĐẾN XA
        """
        import pandas as pd
        df = pd.read_sql(query, self.conn)
        return df.to_dict('records') if not df.empty else []

    def update_screening(self, screening_id, room_id, date_str, time_str):
        """Cập nhật Lịch chiếu (sẽ tự động tính lại giá vé BasePrice theo lịch mới)"""
        import pandas as pd
        date_obj = pd.to_datetime(date_str).date()
        base_price = self.calculate_base_price(date_obj)
        
        query = "UPDATE Screenings SET RoomID = %s, ScreeningDate = %s, ScreeningTime = %s, BasePrice = %s WHERE ScreeningID = %s"
        self.cursor.execute(query, (room_id, date_str, time_str, base_price, screening_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_screening(self, screening_id):
        """Xóa suất chiếu"""
        query = "DELETE FROM Screenings WHERE ScreeningID = %s"
        self.cursor.execute(query, (screening_id))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # =======================================================
    # QUẢN LÝ PHÒNG CHIẾU (CINEMA ROOM MANAGEMENT)
    # =======================================================
    def add_cinema_room_with_seats(self, room_name, room_type, rows, cols):
        """Thêm phòng chiếu mới và tự động sinh sơ đồ ghế vật lý"""
        try:
            capacity = rows * cols
            
            # 1. Thêm phòng chiếu vào bảng CinemaRooms
            query_room = "INSERT INTO CinemaRooms (RoomName, Capacity) VALUES (%s, %s)"
            self.cursor.execute(query_room, (room_name, capacity))
            room_id = self.cursor.lastrowid # Lấy ID phòng vừa tạo
            
            # 2. Lấy mapping loại ghế từ Database
            self.cursor.execute("SELECT TypeName, SeatTypeID FROM SeatTypes")
            type_map = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # 3. Thuật toán tự động sinh Sơ đồ ghế (Seat Layout)
            seats_data = []
            for r in range(rows):
                row_label = chr(65 + r) # Sinh ký tự A, B, C...
                for c in range(1, cols + 1):
                    seat_number = f"{row_label}{c:02d}" # Sinh số 01, 02...
                    
                    # Logic xếp ghế thông minh theo định dạng phòng:
                    if room_type in ['Couple', 'IMAX']: 
                        s_type_id = type_map[room_type]
                    else: 
                        # Đối với phòng thường: Hàng cuối cùng luôn là ghế VIP, còn lại là Standard
                        s_type_id = type_map['VIP'] if r == rows - 1 else type_map['Standard']
                    
                    seats_data.append((room_id, seat_number, s_type_id))
            
            # 4. Ghi hàng loạt (Bulk Insert) ghế vào sơ đồ vật lý
            query_seats = "INSERT INTO Seats (RoomID, SeatNumber, SeatTypeID) VALUES (%s, %s, %s)"
            self.cursor.executemany(query_seats, seats_data)
            self.conn.commit()
            
            return True, f"Tạo phòng '{room_name}' thành công! Đã tự động sinh {capacity} ghế."
        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi hệ thống: {e}"