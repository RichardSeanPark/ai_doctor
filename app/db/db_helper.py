from app.db.database import Database

def get_db_connection():
    """
    데이터베이스 연결을 반환합니다.
    이 함수는 여러 모듈에서 일관된 방식으로 데이터베이스 연결을 가져오기 위해 사용됩니다.
    """
    return Database().connect() 