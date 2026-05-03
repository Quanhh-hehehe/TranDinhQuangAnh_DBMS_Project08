import mysql.connector
from faker import Faker
import random
import bcrypt
import datetime 
from app.config import DB_CONFIG

fake = Faker('en_US')

print("Đang tạo mã băm bảo mật cho dữ liệu mẫu...")
default_password = "123456"
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), salt).decode('utf-8')

# =========================================================
# HÀM LOGIC TÍNH GIÁ VÉ THEO LỊCH 
# =========================================================
def calculate_base_price(date_obj):
    """Tính giá vé cơ sở tự động dựa trên ngày chiếu"""
    # Khai báo các ngày lễ cố định ở Việt Nam (MM-DD)
    holidays = ['01-01', '02-14', '03-08', '04-30', '05-01', '09-02', '10-20', '12-24', '12-25', '12-31']
    month_day = date_obj.strftime('%m-%d')
    
    # 1. Ưu tiên kiểm tra ngày lễ trước (Giảm giá sốc kích cầu)
    if month_day in holidays:
        return 50000.0
    
    # 2. Kiểm tra ngày cuối tuần (weekday: 0=Thứ 2 ... 4=Thứ 6, 5=Thứ 7, 6=CN)
    if date_obj.weekday() >= 4: 
        return 80000.0
    
    # 3. Mặc định ngày thường (Thứ 2 -> Thứ 5)
    return 60000.0

try:
    # =========================================================
    # KẾT NỐI DATABASE BẰNG CONFIG BẢO MẬT TỪ BIẾN MÔI TRƯỜNG
    # =========================================================
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()
    print("Bắt đầu sinh dữ liệu mẫu cho cấu trúc Hybrid nâng cao...\n")

    # ---------------------------------------------------------
    # 1. TẠO TÀI KHOẢN ADMIN VÀ NHÂN VIÊN (BẢNG STAFF)
    # ---------------------------------------------------------
    # Tài khoản 1: Quản lý (Manager)
    admin_pass = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute(
        "INSERT INTO Staff (FullName, Username, Password, Role) VALUES (%s, %s, %s, %s)",
        ("Administrator", "admin", admin_pass, "Manager")
    )
    
    # Tài khoản 2: Nhân viên bán vé (Clerk) - BỔ SUNG ĐỂ PHÂN QUYỀN RBAC
    clerk_pass = bcrypt.hashpw("clerk123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute(
        "INSERT INTO Staff (FullName, Username, Password, Role) VALUES (%s, %s, %s, %s)",
        ("Ticket Clerk", "clerk", clerk_pass, "Clerk")
    )
    
    db.commit()
    print("✅ Đã tạo tài khoản Quản lý (admin) và Nhân viên (clerk).")

    # ---------------------------------------------------------
    # 2. CẤU HÌNH LOẠI GHẾ (SeatTypes)
    # ---------------------------------------------------------
    seat_types_data = [('Standard', 1.00), ('VIP', 1.20), ('Couple', 2.00), ('IMAX', 1.50)]
    cursor.executemany("INSERT INTO SeatTypes (TypeName, PriceMultiplier) VALUES (%s, %s)", seat_types_data)
    db.commit()
    
    cursor.execute("SELECT TypeName, SeatTypeID FROM SeatTypes")
    type_map = {row[0]: row[1] for row in cursor.fetchall()}

    # ---------------------------------------------------------
    # 3. TẠO 510 BỘ PHIM & THỂ LOẠI
    # ---------------------------------------------------------
    base_genres = ['Action', 'Romance', 'Comedy', 'Horror', 'Sci-Fi', 'Animation', 'Documentary', 'Thriller', 'Fantasy']
    genre_map = {}
    
    for genre in base_genres:
        cursor.execute("INSERT INTO Genres (GenreName) VALUES (%s)", (genre,))
        genre_map[genre] = cursor.lastrowid
    db.commit()

    for _ in range(510):
        title = fake.catch_phrase()
        primary_genre = random.choice(base_genres)
        duration = random.randint(80, 190)
        
        cursor.execute("INSERT INTO Movies (MovieTitle, Genre, DurationMinutes) VALUES (%s, %s, %s)", (title, primary_genre, duration))
        movie_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO MovieGenres (MovieID, GenreID) VALUES (%s, %s)", (movie_id, genre_map[primary_genre]))
        extra_genre = random.choice(base_genres)
        if extra_genre != primary_genre:
            cursor.execute("INSERT INTO MovieGenres (MovieID, GenreID) VALUES (%s, %s)", (movie_id, genre_map[extra_genre]))
    db.commit()
    print("✅ Đã chèn 510 Phim.")

    # ---------------------------------------------------------
    # 4. TẠO 510 PHÒNG CHIẾU & GHẾ VẬT LÝ
    # ---------------------------------------------------------
    seats_data = []
    room_configs = [('IMAX', 8, 12), ('Couple', 4, 8), ('VIP', 6, 10), ('Standard 2D', 5, 8)]

    for i in range(1, 511):
        config = random.choice(room_configs)
        r_type, rows, cols = config
        room_name = f"Screen {i:03d} - {r_type}"
        capacity = rows * cols
        
        cursor.execute("INSERT INTO CinemaRooms (RoomName, Capacity) VALUES (%s, %s)", (room_name, capacity))
        room_id = cursor.lastrowid
        
        for r in range(rows):
            row_label = chr(65 + r)
            for c in range(1, cols + 1):
                seat_number = f"{row_label}{c:02d}"
                if r_type in ['Couple', 'IMAX']: s_type_id = type_map[r_type]
                else: s_type_id = type_map['VIP'] if r == rows - 1 else type_map['Standard']
                seats_data.append((room_id, seat_number, s_type_id))

    cursor.executemany("INSERT INTO Seats (RoomID, SeatNumber, SeatTypeID) VALUES (%s, %s, %s)", seats_data)
    db.commit()
    print("✅ Đã chèn 510 Phòng chiếu và sơ đồ ghế.")

    # ---------------------------------------------------------
    # 5. TẠO 510 KHÁCH HÀNG (CÓ USERNAME)
    # ---------------------------------------------------------
    customers_data = []
    usernames = set()
    phones = set()
    
    while len(usernames) < 510:
        u = fake.user_name()
        p = f"0{random.randint(900000000, 999999999)}" # Sinh sdt chuẩn Việt Nam (bắt đầu bằng 0, đủ 10 số)
        if u not in usernames and p not in phones:
            usernames.add(u)
            phones.add(p)
            customers_data.append((fake.name(), u, p, hashed_password))

    cursor.executemany("INSERT INTO Customers (CustomerName, Username, PhoneNumber, Password) VALUES (%s, %s, %s, %s)", customers_data)
    db.commit()
    print("✅ Đã chèn 510 Khách hàng (Pass mặc định: 123456).")

    # ---------------------------------------------------------
    # 6. TẠO 510 SUẤT CHIẾU (ĐÃ NIÊM PHONG GIÁ CƠ SỞ)
    # ---------------------------------------------------------
    cursor.execute("SELECT MovieID FROM Movies")
    movie_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT RoomID FROM CinemaRooms")
    room_ids = [row[0] for row in cursor.fetchall()]

    screenings_data = []
    for _ in range(510):
        m_id = random.choice(movie_ids)
        r_id = random.choice(room_ids)
        # Sinh ngày chiếu ngẫu nhiên từ quá khứ đến tương lai để dễ dính ngày lễ
        date = fake.date_between(start_date='-30d', end_date='+90d')
        time = f"{random.randint(8, 23):02d}:{random.choice(['00', '15', '30', '45'])}:00"
        
        # CẬP NHẬT TÍNH TOÁN BASE PRICE
        base_price = calculate_base_price(date)
        
        screenings_data.append((m_id, r_id, date, time, base_price))

    # Cập nhật câu lệnh INSERT thêm BasePrice
    cursor.executemany("INSERT INTO Screenings (MovieID, RoomID, ScreeningDate, ScreeningTime, BasePrice) VALUES (%s, %s, %s, %s, %s)", screenings_data)
    db.commit()
    print("✅ Đã chèn 510 Suất chiếu (Hệ thống đã tự động tính Base Price).")

    # ---------------------------------------------------------
    # 7. TẠO 510 VÉ ĐẶT (CÓ LỊCH SỬ THỜI GIAN & TRẠNG THÁI VÉ)
    # ---------------------------------------------------------
    # BƯỚC QUAN TRỌNG BỊ THIẾU: Lấy danh sách ghế vật lý của từng phòng
    cursor.execute("SELECT RoomID, SeatNumber FROM Seats")
    room_seats_map = {}
    for r_id, s_num in cursor.fetchall():
        if r_id not in room_seats_map: 
            room_seats_map[r_id] = []
        room_seats_map[r_id].append(s_num)

    # Lấy thêm ScreeningDate và ScreeningTime để tính BookingTime
    cursor.execute("SELECT ScreeningID, RoomID, ScreeningDate, ScreeningTime FROM Screenings")
    screenings_info = cursor.fetchall()

    tickets_data = []
    booked_set = set() # Set này dùng để giả lập chống trùng ghế lúc Import

    while len(tickets_data) < 510:
        c_id = random.randint(1, 510)
        screening = random.choice(screenings_info)
        scr_id, rm_id, scr_date, scr_time = screening[0], screening[1], screening[2], screening[3]
        
        valid_seats = room_seats_map[rm_id]
        chosen_seat_num = random.choice(valid_seats)
        
        # Chỉ những ghế 'Booked' mới bị tính là đã đặt
        if (scr_id, chosen_seat_num) not in booked_set:
            # Random trạng thái: 90% là Booked, 10% là Cancelled
            status = 'Booked' if random.random() < 0.9 else 'Cancelled'
            
            # Nếu Booked, đưa vào danh sách đen chống trùng
            if status == 'Booked':
                booked_set.add((scr_id, chosen_seat_num))
                
            # Tính thời gian đặt vé (BookingTime): Phải đặt trước giờ chiếu từ 1 đến 14 ngày
            # Tính toán thời điểm phim chiếu
            if isinstance(scr_time, datetime.timedelta):
                # Nếu scr_time là timedelta (thường gặp trong thư viện mysql-connector)
                scr_datetime = datetime.datetime.combine(scr_date, datetime.datetime.min.time()) + scr_time
            else:
                # Nếu scr_time là dạng khác, ta an toàn parse từ chuỗi
                scr_datetime = datetime.datetime.combine(scr_date, datetime.time())

            days_before = random.randint(1, 14)
            hours_before = random.randint(1, 23)
            booking_time = scr_datetime - datetime.timedelta(days=days_before, hours=hours_before)

            tickets_data.append((c_id, scr_id, chosen_seat_num, booking_time.strftime('%Y-%m-%d %H:%M:%S'), status))

    cursor.executemany("INSERT INTO Tickets (CustomerID, ScreeningID, SeatNumber, BookingTime, TicketStatus) VALUES (%s, %s, %s, %s, %s)", tickets_data)
    db.commit()
    print("✅ Đã chèn 510 Vé (Bao gồm dữ liệu BookingTime và Trạng thái Cancelled).")

except mysql.connector.Error as err:
    print(f"❌ LỖI DATABASE: {err}")
except Exception as e:
    print(f"❌ LỖI HỆ THỐNG: {e}")
finally:
    if 'cursor' in locals() and cursor is not None: cursor.close()
    if 'db' in locals() and db.is_connected(): db.close()