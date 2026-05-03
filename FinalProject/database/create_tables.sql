-- =============================================================
-- CINEMA MANAGEMENT SYSTEM - HYBRID SCHEMA (ĐÚNG YÊU CẦU ĐỀ BÀI)
-- =============================================================

CREATE DATABASE IF NOT EXISTS CinemaManagement;
USE CinemaManagement;

-- Xóa bảng cũ theo thứ tự ngược lại của khóa ngoại
DROP TABLE IF EXISTS Tickets;
DROP TABLE IF EXISTS Screenings;
DROP TABLE IF EXISTS Staff; 
DROP TABLE IF EXISTS MovieGenres;
DROP TABLE IF EXISTS Genres;
DROP TABLE IF EXISTS Seats;
DROP TABLE IF EXISTS SeatTypes;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS CinemaRooms;
DROP TABLE IF EXISTS Movies;

-- =============================================================
-- PHẦN 1: 5 BẢNG CỐT LÕI (CHUẨN 100% THEO ẢNH YÊU CẦU)
-- =============================================================

-- 1. Bảng Phim (Giữ lại cột Genre theo đúng ảnh)
CREATE TABLE Movies (
    MovieID INT AUTO_INCREMENT PRIMARY KEY,
    MovieTitle VARCHAR(255) NOT NULL,
    Genre VARCHAR(100),
    DurationMinutes INT NOT NULL CHECK (DurationMinutes > 0)
);

-- 2. Bảng Phòng chiếu 
CREATE TABLE CinemaRooms (
    RoomID INT AUTO_INCREMENT PRIMARY KEY,
    RoomName VARCHAR(100) NOT NULL,
    Capacity INT NOT NULL CHECK (Capacity > 0)
);

-- 3. Bảng Khách hàng 
CREATE TABLE Customers (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerName VARCHAR(255) NOT NULL,
    Username VARCHAR(50) UNIQUE NOT NULL, 
    PhoneNumber VARCHAR(20) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL DEFAULT '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/zBJuBJkeEZ6E44ycS.nYqT.69.'
);

-- 2. Bảng Nhân viên/Quản lý 
CREATE TABLE Staff (
    StaffID INT AUTO_INCREMENT PRIMARY KEY,
    FullName VARCHAR(255) NOT NULL,
    Username VARCHAR(50) UNIQUE NOT NULL, -- Tên đăng nhập admin
    Password VARCHAR(255) NOT NULL,
    Role VARCHAR(20) DEFAULT 'Manager' -- Phân quyền: Manager, Clerk...
);

-- 4. Bảng Suất chiếu 
CREATE TABLE Screenings (
    ScreeningID INT AUTO_INCREMENT PRIMARY KEY,
    MovieID INT NOT NULL,
    RoomID INT NOT NULL,
    ScreeningDate DATE NOT NULL,
    ScreeningTime TIME NOT NULL,
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE,
    FOREIGN KEY (RoomID) REFERENCES CinemaRooms(RoomID) ON DELETE CASCADE
);

-- 1. Thêm cột giá vé niêm phong vào bảng Suất chiếu
ALTER TABLE Screenings ADD COLUMN BasePrice DECIMAL(10, 2) NOT NULL DEFAULT 60000.00;
DROP FUNCTION IF EXISTS fn_GetScreeningRevenue;
DELIMITER $$
CREATE FUNCTION fn_GetScreeningRevenue(p_ScreeningID INT) 
RETURNS DECIMAL(15,2)
DETERMINISTIC
BEGIN
    DECLARE v_TotalRevenue DECIMAL(15,2);
    
    -- Lấy BasePrice trực tiếp từ bảng Screenings của chính suất chiếu đó
    SELECT SUM(s.BasePrice * st.PriceMultiplier) INTO v_TotalRevenue
    FROM Tickets t
    JOIN Screenings s ON t.ScreeningID = s.ScreeningID
    JOIN Seats se ON s.RoomID = se.RoomID AND t.SeatNumber = se.SeatNumber
    JOIN SeatTypes st ON se.SeatTypeID = st.SeatTypeID
    WHERE t.ScreeningID = p_ScreeningID;
    
    RETURN IFNULL(v_TotalRevenue, 0);
END$$
DELIMITER ;

-- 5. Bảng Vé 
CREATE TABLE Tickets (
    TicketID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    ScreeningID INT NOT NULL,
    SeatNumber VARCHAR(10) NOT NULL,
    BookingTime DATETIME NOT NULL, 
    TicketStatus VARCHAR(20) NOT NULL DEFAULT 'Booked',
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE,
    FOREIGN KEY (ScreeningID) REFERENCES Screenings(ScreeningID) ON DELETE CASCADE
);

-- =============================================================
-- PHẦN 2: 4 BẢNG NÂNG CAO 
-- =============================================================

-- 6. Bảng Thể loại (Chuẩn hóa từ cột Genre của bảng Movies)
CREATE TABLE Genres (
    GenreID INT AUTO_INCREMENT PRIMARY KEY,
    GenreName VARCHAR(100) UNIQUE NOT NULL
);

-- 7. Bảng Trung gian Phim - Thể loại (Phục vụ truy vấn đa thể loại)
CREATE TABLE MovieGenres (
    MovieID INT NOT NULL,
    GenreID INT NOT NULL,
    PRIMARY KEY (MovieID, GenreID),
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE,
    FOREIGN KEY (GenreID) REFERENCES Genres(GenreID) ON DELETE CASCADE
);

-- 8. Bảng Loại ghế & Hệ số giá (Để hàm tính tiền tự động lấy hệ số)
CREATE TABLE SeatTypes (
    SeatTypeID INT AUTO_INCREMENT PRIMARY KEY,
    TypeName VARCHAR(50) NOT NULL, 
    PriceMultiplier DECIMAL(4,2) DEFAULT 1.00 
);

-- 9. Bảng Ghế vật lý (Quản lý sơ đồ ghế thực tế)
CREATE TABLE Seats (
    SeatID INT AUTO_INCREMENT PRIMARY KEY,
    RoomID INT NOT NULL,
    SeatNumber VARCHAR(10) NOT NULL, 
    SeatTypeID INT NOT NULL,
    FOREIGN KEY (RoomID) REFERENCES CinemaRooms(RoomID) ON DELETE CASCADE,
    FOREIGN KEY (SeatTypeID) REFERENCES SeatTypes(SeatTypeID),
    UNIQUE (RoomID, SeatNumber) -- Một phòng không thể có 2 ghế trùng tên
);