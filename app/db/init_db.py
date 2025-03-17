"""
데이터베이스 초기화 스크립트
필요한 테이블을 생성합니다.
"""

import logging
from app.db.database import Database

logger = logging.getLogger(__name__)

def init_database():
    """데이터베이스 테이블 초기화"""
    db = Database()
    
    # 사용자 테이블 생성
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(36) PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name VARCHAR(100),
        birth_date DATE,
        gender VARCHAR(10),
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 세션 테이블 생성
    create_sessions_table = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 건강 지표 테이블 생성
    create_health_metrics_table = """
    CREATE TABLE IF NOT EXISTS health_metrics (
        metrics_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        weight FLOAT,
        height FLOAT,
        heart_rate INT,
        blood_pressure_systolic INT,
        blood_pressure_diastolic INT,
        blood_sugar FLOAT,
        temperature FLOAT,
        oxygen_saturation INT,
        sleep_hours FLOAT,
        steps INT,
        bmi FLOAT,
        gemini_response TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 식이 제한 테이블 생성
    create_dietary_restrictions_table = """
    CREATE TABLE IF NOT EXISTS dietary_restrictions (
        restriction_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        restriction_type VARCHAR(50) NOT NULL,
        description VARCHAR(255) NOT NULL,
        severity VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 식단 조언 기록 테이블 생성
    create_diet_advice_history_table = """
    CREATE TABLE IF NOT EXISTS diet_advice_history (
        advice_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        request_id VARCHAR(20) NOT NULL,
        meal_date DATE NOT NULL,
        meal_type VARCHAR(20) NOT NULL,
        food_items JSON NOT NULL,
        dietary_restrictions JSON,
        health_goals JSON,
        specific_concerns TEXT,
        advice_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_meal (user_id, meal_date, meal_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    try:
        # 테이블 생성 실행
        db.execute_query(create_users_table)
        logger.info("사용자 테이블 생성 완료")
        
        db.execute_query(create_sessions_table)
        logger.info("세션 테이블 생성 완료")
        
        db.execute_query(create_health_metrics_table)
        logger.info("건강 지표 테이블 생성 완료")
        
        db.execute_query(create_dietary_restrictions_table)
        logger.info("식이 제한 테이블 생성 완료")
        
        db.execute_query(create_diet_advice_history_table)
        logger.info("식단 조언 기록 테이블 생성 완료")
        
        return True
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {e}")
        return False

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 데이터베이스 초기화 실행
    success = init_database()
    if success:
        print("데이터베이스 초기화 완료")
    else:
        print("데이터베이스 초기화 실패") 