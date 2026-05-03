-- =============================================================
-- 04_FUNCTIONS.SQL: USER DEFINED FUNCTIONS (BUSINESS LOGIC)
-- ĐÁP ỨNG YÊU CẦU: "Calculate occupancy rate or total revenue per screening"
-- =============================================================

USE CinemaManagement;

-- 1. Hàm tính Tổng doanh thu của một suất chiếu (Total Revenue)
DROP FUNCTION IF EXISTS fn_GetScreeningRevenue;

DELIMITER $$
CREATE FUNCTION fn_GetScreeningRevenue(
    p_ScreeningID INT, 
    p_BasePrice DECIMAL(10,2) -- Giá vé cơ bản (VD: 50000)
) 
RETURNS DECIMAL(15,2)
READS SQL DATA 
BEGIN
    DECLARE v_TotalRevenue DECIMAL(15,2) DEFAULT 0.00;
    DECLARE v_RoomID INT;
    
    -- Bước 1: Lấy RoomID của suất chiếu này để mapping đúng sơ đồ ghế
    SELECT RoomID INTO v_RoomID FROM Screenings WHERE ScreeningID = p_ScreeningID;
    
    -- Bước 2: Tính tổng tiền bằng cách kết nối SeatNumber với sơ đồ ghế vật lý
    SELECT IFNULL(SUM(p_BasePrice * st.PriceMultiplier), 0)
    INTO v_TotalRevenue
    FROM Tickets t
    JOIN Seats s ON t.SeatNumber = s.SeatNumber AND s.RoomID = v_RoomID
    JOIN SeatTypes st ON s.SeatTypeID = st.SeatTypeID
    WHERE t.ScreeningID = p_ScreeningID;
    
    RETURN v_TotalRevenue;
END$$
DELIMITER ;

-- 2. Hàm tính Tỷ lệ lấp đầy của một suất chiếu (Occupancy Rate)
DROP FUNCTION IF EXISTS fn_CalculateOccupancyRate;

DELIMITER $$
CREATE FUNCTION fn_CalculateOccupancyRate(
    p_ScreeningID INT
) 
RETURNS DECIMAL(5,2)
READS SQL DATA 
BEGIN
    DECLARE v_Capacity INT DEFAULT 0;
    DECLARE v_TicketsSold INT DEFAULT 0;
    DECLARE v_Rate DECIMAL(5,2) DEFAULT 0.00;
    
    -- Lấy sức chứa tối đa của phòng chiếu
    SELECT c.Capacity INTO v_Capacity
    FROM Screenings s
    JOIN CinemaRooms c ON s.RoomID = c.RoomID
    WHERE s.ScreeningID = p_ScreeningID;
    
    -- Lấy số lượng vé đã bán
    SELECT COUNT(*) INTO v_TicketsSold
    FROM Tickets
    WHERE ScreeningID = p_ScreeningID;
    
    -- Tính tỷ lệ phần trăm (Tránh lỗi chia cho 0)
    IF v_Capacity > 0 THEN
        SET v_Rate = (v_TicketsSold / v_Capacity) * 100;
    END IF;
    
    RETURN ROUND(v_Rate, 2);
END$$
DELIMITER ;