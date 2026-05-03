-- =============================================================
-- 06_SECURITY.SQL: ENTERPRISE ROLE-BASED ACCESS CONTROL (RBAC)
-- ĐÁP ỨNG YÊU CẦU: "Assign roles and control access to sensitive data"
-- =============================================================

USE CinemaManagement;

-- 1. Xóa Roles và Users cũ (nếu có) để làm mới
DROP ROLE IF EXISTS 'admin_role', 'app_service_role', 'data_analyst_role';
DROP USER IF EXISTS 'cinema_admin'@'localhost', 'python_app'@'localhost', 'data_analyst'@'localhost';

-- 2. Tạo Roles mới
CREATE ROLE 'admin_role', 'app_service_role', 'data_analyst_role';

-- ====================================================================
-- ROLE 1: ADMIN (Quản trị viên Hệ thống) - Toàn quyền
-- ====================================================================
GRANT ALL PRIVILEGES ON CinemaManagement.* TO 'admin_role';

-- ====================================================================
-- ROLE 2: APP SERVICE (Nhân viên / App Python Backend)
-- Đảm bảo nguyên tắc "Quyền tối thiểu" (Least Privilege)
-- ====================================================================
-- Cấp quyền ĐỌC (SELECT) trên các bảng cốt lõi và bảng Hybrid
GRANT SELECT ON CinemaManagement.Customers TO 'app_service_role';
GRANT SELECT ON CinemaManagement.Tickets TO 'app_service_role';
GRANT SELECT ON CinemaManagement.Movies TO 'app_service_role';
GRANT SELECT ON CinemaManagement.Screenings TO 'app_service_role';
GRANT SELECT ON CinemaManagement.CinemaRooms TO 'app_service_role';
GRANT SELECT ON CinemaManagement.Genres TO 'app_service_role';
GRANT SELECT ON CinemaManagement.MovieGenres TO 'app_service_role';
GRANT SELECT ON CinemaManagement.Seats TO 'app_service_role';
GRANT SELECT ON CinemaManagement.SeatTypes TO 'app_service_role';

-- Cấp quyền ĐỌC trên View Lịch chiếu
GRANT SELECT ON CinemaManagement.v_ScreeningSchedule TO 'app_service_role';

-- Quyền Tạo tài khoản mới (Menu 2)
GRANT INSERT ON CinemaManagement.Customers TO 'app_service_role';

-- Quyền Hủy Vé (Menu 3)
GRANT DELETE ON CinemaManagement.Tickets TO 'app_service_role';

-- Quyền Thực thi Stored Procedures (Bắt buộc cho Menu 2)
GRANT EXECUTE ON PROCEDURE CinemaManagement.sp_BookTicket TO 'app_service_role';
GRANT EXECUTE ON PROCEDURE CinemaManagement.sp_GetAvailableSeats TO 'app_service_role';

-- Quyền Thực thi Functions (Bắt buộc cho Menu 4)
GRANT EXECUTE ON FUNCTION CinemaManagement.fn_GetScreeningRevenue TO 'app_service_role';

-- ====================================================================
-- ROLE 3: DATA ANALYST (Chuyên viên Phân tích Báo cáo)
-- Chỉ được xem báo cáo tổng hợp, không được xem số điện thoại/password
-- ====================================================================
GRANT SELECT ON CinemaManagement.v_ScreeningSchedule TO 'data_analyst_role';
GRANT SELECT ON CinemaManagement.v_OccupancyReport TO 'data_analyst_role';
GRANT SELECT ON CinemaManagement.v_RevenueDetail TO 'data_analyst_role';
GRANT EXECUTE ON FUNCTION CinemaManagement.fn_GetScreeningRevenue TO 'data_analyst_role';
GRANT EXECUTE ON FUNCTION CinemaManagement.fn_CalculateOccupancyRate TO 'data_analyst_role';

-- ====================================================================
-- 3. Tạo User thực tế và Gán Role
-- ====================================================================
CREATE USER 'cinema_admin'@'localhost' IDENTIFIED BY 'Admin@2026_Secure';
CREATE USER 'python_app'@'localhost' IDENTIFIED BY 'App@2026_Backend';
CREATE USER 'data_analyst'@'localhost' IDENTIFIED BY 'Analyst@123';

GRANT 'admin_role' TO 'cinema_admin'@'localhost';
GRANT 'app_service_role' TO 'python_app'@'localhost';
GRANT 'data_analyst_role' TO 'data_analyst'@'localhost';

-- 4. Kích hoạt Role mặc định khi User đăng nhập
SET DEFAULT ROLE 'admin_role' TO 'cinema_admin'@'localhost';
SET DEFAULT ROLE 'app_service_role' TO 'python_app'@'localhost';
SET DEFAULT ROLE 'data_analyst_role' TO 'data_analyst'@'localhost';

FLUSH PRIVILEGES;