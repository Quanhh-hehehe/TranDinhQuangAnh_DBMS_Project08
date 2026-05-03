-- =============================================================
-- 03_PROCEDURES.SQL: TRANSACTION & BUSINESS LOGIC
-- ĐÁP ỨNG YÊU CẦU: "Automate ticket booking or check seat availability"
-- =============================================================

USE CinemaManagement;

-- 1. Thủ tục Đặt vé an toàn (sp_BookTicket)
-- Tự động hóa việc kiểm tra ghế có tồn tại không và có bị trùng không
USE CinemaManagement;

DROP PROCEDURE IF EXISTS sp_BookTicket;

DELIMITER $$
CREATE PROCEDURE sp_BookTicket(
    IN p_CustomerID INT,
    IN p_ScreeningID INT,
    IN p_SeatNumber VARCHAR(10)
)
BEGIN
    DECLARE v_RoomID INT;
    DECLARE v_SeatExists INT DEFAULT 0;
    DECLARE v_IsBooked INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Lỗi hệ thống khi đặt vé. Vui lòng thử lại!';
    END;

    START TRANSACTION;

    SELECT RoomID INTO v_RoomID FROM Screenings WHERE ScreeningID = p_ScreeningID;

    SELECT COUNT(*) INTO v_SeatExists 
    FROM Seats 
    WHERE RoomID = v_RoomID AND SeatNumber = UPPER(TRIM(p_SeatNumber));

    IF v_SeatExists = 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ghế không tồn tại trong sơ đồ phòng chiếu này!';
    ELSE
        -- 🛠️ BẢN VÁ 1: Chỉ đếm những vé 'Booked' để chống trùng
        SELECT COUNT(*) INTO v_IsBooked 
        FROM Tickets 
        WHERE ScreeningID = p_ScreeningID AND SeatNumber = UPPER(TRIM(p_SeatNumber)) AND TicketStatus = 'Booked'
        FOR UPDATE;

        IF v_IsBooked > 0 THEN
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ghế này đã có người đặt! Vui lòng chọn ghế khác.';
        ELSE
            -- BẢN VÁ 2: Khai báo đầy đủ 5 cột, dùng NOW() cho BookingTime
            INSERT INTO Tickets (CustomerID, ScreeningID, SeatNumber, BookingTime, TicketStatus)
            VALUES (p_CustomerID, p_ScreeningID, UPPER(TRIM(p_SeatNumber)), NOW(), 'Booked');
            COMMIT;
        END IF;
    END IF;
END$$
DELIMITER ;

-- 2. Thủ tục Kiểm tra ghế trống (sp_GetAvailableSeats)
-- Trả về danh sách các ghế vật lý chưa được mua cho một suất chiếu cụ thể
-- 2. Thủ tục Kiểm tra ghế trống (sp_GetAvailableSeats)
DROP PROCEDURE IF EXISTS sp_GetAvailableSeats;

DELIMITER $$
CREATE PROCEDURE sp_GetAvailableSeats(IN p_ScreeningID INT)
BEGIN
    DECLARE v_RoomID INT;
    
    SELECT RoomID INTO v_RoomID FROM Screenings WHERE ScreeningID = p_ScreeningID;

    -- Lấy tất cả ghế trong phòng đó TRỪ đi những ghế đã 'Booked'
    SELECT s.SeatNumber, st.TypeName, st.PriceMultiplier
    FROM Seats s
    JOIN SeatTypes st ON s.SeatTypeID = st.SeatTypeID
    WHERE s.RoomID = v_RoomID
    AND s.SeatNumber NOT IN (
        -- BỔ SUNG: Chỉ loại trừ những ghế đang có người đặt thực sự
        SELECT SeatNumber FROM Tickets 
        WHERE ScreeningID = p_ScreeningID AND TicketStatus = 'Booked'
    )
    ORDER BY s.SeatNumber;
END$$
DELIMITER ;