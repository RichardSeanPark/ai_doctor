"""
데이터베이스 초기화 스크립트
"""
import os
import logging
import pymysql
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 데이터베이스 접속 정보
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "healthai")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "healthai_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

def create_database():
    """데이터베이스가 없는 경우 생성"""
    try:
        # 데이터베이스 없이 연결
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            charset=DB_CHARSET
        )
        
        cursor = conn.cursor()
        
        # 데이터베이스 존재 여부 확인
        cursor.execute(f"SHOW DATABASES LIKE '{DB_NAME}'")
        result = cursor.fetchone()
        
        # 데이터베이스가 없으면 생성
        if not result:
            cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci")
            logger.info(f"데이터베이스 '{DB_NAME}' 생성 완료")
        else:
            logger.info(f"데이터베이스 '{DB_NAME}'가 이미 존재합니다")
            
        conn.close()
        return True
    except Exception as e:
        logger.error(f"데이터베이스 생성 중 오류 발생: {str(e)}")
        return False

def init_tables():
    """스키마 파일에서 테이블 생성"""
    try:
        # 데이터베이스 연결
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            port=DB_PORT,
            charset=DB_CHARSET
        )
        
        cursor = conn.cursor()
        
        # 스키마 파일 읽기
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # 각 SQL 문 실행
        statements = schema_sql.split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
                
        conn.commit()
        conn.close()
        logger.info("테이블 생성 완료")
        return True
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {str(e)}")
        return False

def main():
    """데이터베이스 초기화 메인 함수"""
    logger.info("데이터베이스 초기화 시작")
    
    if create_database():
        if init_tables():
            logger.info("데이터베이스 초기화 완료")
        else:
            logger.error("테이블 생성 실패")
    else:
        logger.error("데이터베이스 생성 실패")

if __name__ == "__main__":
    main() 