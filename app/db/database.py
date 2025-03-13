import pymysql
from pymysql.cursors import DictCursor
import logging
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    """데이터베이스 연결 및 쿼리 실행을 담당하는 클래스"""
    
    _instance = None
    
    def __new__(cls):
        """싱글톤 패턴으로 구현"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """데이터베이스 연결 설정"""
        if self._initialized:
            return
            
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "health_app")
        self.password = os.getenv("DB_PASSWORD", "")
        self.db = os.getenv("DB_NAME", "health_ai_db")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.charset = "utf8mb4"
        
        # 연결 풀 (connection pool)
        self.pool = None
        self._connection = None
        self._initialized = True
        
        logger.info(f"데이터베이스 연결 초기화: {self.db}@{self.host}")
    
    def connect(self):
        """데이터베이스 연결 수립"""
        try:
            if self._connection is None or not self._connection.open:
                self._connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    db=self.db,
                    port=self.port,
                    charset=self.charset,
                    cursorclass=DictCursor
                )
                logger.info("데이터베이스 연결 성공")
            return self._connection
        except pymysql.Error as e:
            logger.error(f"데이터베이스 연결 오류: {e}")
            raise
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None
            logger.info("데이터베이스 연결 종료")
    
    def execute_query(self, query: str, params: tuple = None) -> int:
        """쓰기 쿼리 실행 (INSERT, UPDATE, DELETE)"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                conn.commit()
                return affected_rows
        except pymysql.Error as e:
            conn.rollback()
            logger.error(f"쿼리 실행 오류: {e}, 쿼리: {query}, 파라미터: {params}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """단일 레코드 조회"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except pymysql.Error as e:
            logger.error(f"쿼리 실행 오류: {e}, 쿼리: {query}, 파라미터: {params}")
            raise
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """다중 레코드 조회"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.Error as e:
            logger.error(f"쿼리 실행 오류: {e}, 쿼리: {query}, 파라미터: {params}")
            raise
    
    def insert_and_get_id(self, query: str, params: tuple = None) -> int:
        """INSERT 쿼리 실행 후 생성된 ID 반환"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                last_id = cursor.lastrowid
                conn.commit()
                return last_id
        except pymysql.Error as e:
            conn.rollback()
            logger.error(f"쿼리 실행 오류: {e}, 쿼리: {query}, 파라미터: {params}")
            raise 