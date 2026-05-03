-- =============================================================
-- 05_TRIGGERS.SQL: AUTOMATED RULES AND DATA INTEGRITY
-- ĐÁP ỨNG YÊU CẦU: "Notify overbooking" & Đảm bảo tính toàn vẹn dữ liệu
-- =============================================================

USE CinemaManagement;

-- =====================================================================
-- 1. TRIGGER: NGĂN CHẶN CHÁY VÉ (PREVENT OVERBOOKING)
-- Tự động tính toán và chặn lại nếu số lượng vé xuất ra vượt quá sức chứa
-- =====================================================================
DROP TRIGGER IF EXISTS trg_PreventOverbooking;

DELIMITER $$
CREATE TRIGGER trg_PreventOverbooking
BEFORE INSERT ON Tickets
FOR EACH ROW
BEGIN
    DECLARE v_MaxCapacity INT;
    DECLARE v_CurrentSold INT;

    -- Lấy sức chứa tối đa (Capacity) của phòng chiếu cho suất chiếu này
    SELECT c.Capacity INTO v_MaxCapacity 
    FROM Screenings s 
    JOIN CinemaRooms c ON s.RoomID = c.RoomID 
    WHERE s.ScreeningID = NEW.ScreeningID;

    -- Đếm số vé ĐÃ BÁN cho suất chiếu này
    SELECT COUNT(*) INTO v_CurrentSold 
    FROM Tickets 
    WHERE ScreeningID = NEW.ScreeningID;

    -- Nếu số vé đã bán >= sức chứa, ném ra thông báo lỗi và hủy giao dịch Insert
    IF v_CurrentSold >= v_MaxCapacity THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Thất bại: Rạp chiếu này đã đạt tối đa sức chứa (Hết vé)!';
    END IF;
    
END$$
DELIMITER ;


-- =====================================================================
-- 2. TRIGGER: KIỂM TRA TÍNH HỢP LỆ CỦA GHẾ (VALIDATE SEAT EXISTENCE)
-- Sức mạnh của Hybrid Schema: Đảm bảo SeatNumber nhập vào phải có thật!
-- =====================================================================
DROP TRIGGER IF EXISTS trg_ValidateSeatExistence;

DELIMITER $$
CREATE TRIGGER trg_ValidateSeatExistence
BEFORE INSERT ON Tickets
FOR EACH ROW
BEGIN
    DECLARE v_RoomID INT;
    DECLARE v_SeatExists INT DEFAULT 0;

    -- Chuẩn hóa dữ liệu đầu vào: Viết hoa và xóa khoảng trắng thừa (VD: ' a05 ' -> 'A05')
    SET NEW.SeatNumber = UPPER(TRIM(NEW.SeatNumber));

    -- Lấy RoomID của suất chiếu đang được đặt
    SELECT RoomID INTO v_RoomID 
    FROM Screenings 
    WHERE ScreeningID = NEW.ScreeningID;

    -- Đối chiếu SeatNumber với bảng Seats nâng cao xem ghế này có thật trong phòng không
    SELECT COUNT(*) INTO v_SeatExists
    FROM Seats
    WHERE RoomID = v_RoomID AND SeatNumber = NEW.SeatNumber;

    -- Nếu ghế không tồn tại, ném ra lỗi!
    IF v_SeatExists = 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Thất bại: Mã ghế bạn chọn không tồn tại trong sơ đồ rạp này!';
    END IF;

END$$
DELIMITER ;