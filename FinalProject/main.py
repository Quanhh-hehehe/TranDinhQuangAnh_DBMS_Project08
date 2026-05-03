import logging

logging.basicConfig(
    filename='cinema_app.log', 
    level=logging.INFO,        
    format='[%(asctime)s] %(levelname)s: %(message)s', 
    encoding='utf-8'           
)

logging.info("Hệ thống Cinema Management System đang khởi động...")
from app.controller import CinemaController

if __name__ == "__main__":
    app = CinemaController()
    app.start()
    
    
    
    