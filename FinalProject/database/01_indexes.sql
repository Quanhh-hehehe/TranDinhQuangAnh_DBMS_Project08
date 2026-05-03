-- =============================================================
-- 01_INDEXES.SQL: DATABASE PERFORMANCE OPTIMIZATION
-- ĐÁP ỨNG YÊU CẦU: "Speed up queries on movie titles, screening schedules"
-- =============================================================

USE CinemaManagement;

-- 1. Tối ưu hóa tìm kiếm khách hàng đăng nhập (Bảo mật & Tốc độ)
CREATE UNIQUE INDEX idx_customer_phone ON Customers(PhoneNumber);

-- 2. ĐÁP ỨNG YÊU CẦU: Tăng tốc độ tìm kiếm tên phim và thể loại
CREATE INDEX idx_movie_title ON Movies(MovieTitle);
CREATE INDEX idx_movie_genre ON Movies(Genre);

-- 3. ĐÁP ỨNG YÊU CẦU: Tăng tốc độ truy vấn lịch chiếu (Screening schedules)
-- Kết hợp cả MovieID và Ngày chiếu vì người dùng thường chọn Phim -> Chọn Ngày
CREATE INDEX idx_screening_movie_date ON Screenings(MovieID, ScreeningDate);

-- 4. Tối ưu hóa chức năng kiểm tra ghế (chống đặt trùng)
CREATE INDEX idx_ticket_screening_seat ON Tickets(ScreeningID, SeatNumber);

-- 5. Tối ưu hóa tính năng tra cứu lịch sử vé của khách hàng (Menu 3 trong Python)
CREATE INDEX idx_ticket_customer ON Tickets(CustomerID);

-- 6. Tối ưu hóa cho các bảng nâng cao (Hybrid) để lấy thông tin ghế vật lý nhanh hơn
CREATE INDEX idx_seats_room_number ON Seats(RoomID, SeatNumber);