-- =============================================================
-- 02_VIEWS.SQL: VIRTUAL TABLES FOR DASHBOARDS & REPORTING
-- ĐÁP ỨNG YÊU CẦU: "Summaries of daily screenings or available seats"
-- =============================================================

USE CinemaManagement;

-- 1. View tóm tắt lịch chiếu hàng ngày (Daily Screenings Summary)
-- Kết hợp thông tin từ Movies, Screenings và CinemaRooms
CREATE OR REPLACE VIEW v_ScreeningSchedule AS
SELECT 
    s.ScreeningID,
    m.MovieTitle,
    m.Genre,           
    m.DurationMinutes,
    c.RoomName,
    s.ScreeningDate,
    s.ScreeningTime
FROM Screenings s
JOIN Movies m ON s.MovieID = m.MovieID
JOIN CinemaRooms c ON s.RoomID = c.RoomID;

-- 2. View báo cáo ghế trống và tỷ lệ lấp đầy (Available Seats Summary)
-- Giúp quản lý biết rạp nào còn bao nhiêu chỗ, đã bán bao nhiêu vé
CREATE OR REPLACE VIEW v_OccupancyReport AS
SELECT 
    s.ScreeningID,
    m.MovieTitle,
    s.ScreeningDate,
    s.ScreeningTime,
    c.RoomName,
    c.Capacity AS TotalSeats,
    COUNT(t.TicketID) AS TicketsSold,
    (c.Capacity - COUNT(t.TicketID)) AS RemainingSeats,
    ROUND((COUNT(t.TicketID) / c.Capacity) * 100, 2) AS OccupancyRate_Pct
FROM Screenings s
JOIN Movies m ON s.MovieID = m.MovieID
JOIN CinemaRooms c ON s.RoomID = c.RoomID
-- BỔ SUNG: Chỉ đếm những vé có trạng thái 'Booked'
LEFT JOIN Tickets t ON s.ScreeningID = t.ScreeningID AND t.TicketStatus = 'Booked' 
GROUP BY 
    s.ScreeningID, 
    m.MovieTitle, 
    s.ScreeningDate,
    s.ScreeningTime,
    c.RoomName, 
    c.Capacity;

-- 3. View chi tiết doanh thu (Tận dụng bảng SeatTypes nâng cao)
CREATE OR REPLACE VIEW v_RevenueDetail AS
SELECT 
    s.ScreeningID,
    m.MovieTitle,
    c.RoomName,
    SUM(st.PriceMultiplier) AS TotalMultiplier, 
    COUNT(t.TicketID) AS TicketsSold
FROM Screenings s
JOIN Movies m ON s.MovieID = m.MovieID
JOIN CinemaRooms c ON s.RoomID = c.RoomID
-- BỔ SUNG: Chỉ tính tiền những vé 'Booked'
JOIN Tickets t ON s.ScreeningID = t.ScreeningID AND t.TicketStatus = 'Booked'
JOIN Seats se ON (t.SeatNumber = se.SeatNumber AND c.RoomID = se.RoomID)
JOIN SeatTypes st ON se.SeatTypeID = st.SeatTypeID
GROUP BY s.ScreeningID, m.MovieTitle, c.RoomName;