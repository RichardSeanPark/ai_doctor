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
    
    # 소셜 계정 테이블 생성 (주 테이블)
    create_social_accounts_table = """
    CREATE TABLE IF NOT EXISTS social_accounts (
        user_id VARCHAR(36) PRIMARY KEY,
        social_id VARCHAR(255) NOT NULL,
        provider VARCHAR(20) NOT NULL,
        birth_date DATE,
        gender VARCHAR(10),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uk_social_account (social_id, provider)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 세션 테이블 생성
    create_sessions_table = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE
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
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE
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
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE
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
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_meal (user_id, meal_date, meal_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # exercise_recommendations 테이블
    create_exercise_recommendations_table = """
    CREATE TABLE IF NOT EXISTS exercise_recommendations (
        recommendation_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        goal TEXT NOT NULL,
        fitness_level VARCHAR(50),
        recommended_frequency VARCHAR(50),
        exercise_plans JSON NOT NULL,
        special_instructions JSON,
        recommendation_summary TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exercise_location VARCHAR(100),
        preferred_exercise_type VARCHAR(100),
        available_equipment JSON,
        time_per_session INT,
        experience_level VARCHAR(50),
        intensity_preference VARCHAR(50),
        exercise_constraints JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 운동 완료 기록 테이블 생성
    create_exercise_completions_table = """
    CREATE TABLE IF NOT EXISTS exercise_completions (
        completion_id VARCHAR(36) PRIMARY KEY,
        recommendation_id VARCHAR(36) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        completed_at TIMESTAMP NOT NULL,
        satisfaction_rating TINYINT NULL COMMENT '1-5 평점',
        feedback TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recommendation_id) REFERENCES exercise_recommendations(recommendation_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES social_accounts(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 앱 버전 관리 테이블 생성
    create_app_versions_table = """
    CREATE TABLE IF NOT EXISTS app_versions (
        version_code INT NOT NULL,
        version_name VARCHAR(20) NOT NULL,
        min_api_level INT DEFAULT 21,
        force_update BOOLEAN DEFAULT FALSE,
        change_log TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (version_code)
    )
    """
    
    try:
        # 테이블 생성 실행
        db.execute_query(create_social_accounts_table)
        logger.info("소셜 계정 테이블 생성 완료")
        
        db.execute_query(create_sessions_table)
        logger.info("세션 테이블 생성 완료")
        
        db.execute_query(create_health_metrics_table)
        logger.info("건강 지표 테이블 생성 완료")
        
        db.execute_query(create_dietary_restrictions_table)
        logger.info("식이 제한 테이블 생성 완료")
        
        db.execute_query(create_diet_advice_history_table)
        logger.info("식단 조언 기록 테이블 생성 완료")
        
        db.execute_query(create_exercise_recommendations_table)
        logger.info("exercise_recommendations 테이블 생성 완료")
        
        db.execute_query(create_exercise_completions_table)
        logger.info("exercise_completions 테이블 생성 완료")
        
        db.execute_query(create_app_versions_table)
        logger.info("app_versions 테이블 생성 완료")
        
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