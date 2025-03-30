import logging
from app.db.database import Database

logger = logging.getLogger(__name__)

class AppDAO:
    """안드로이드 앱 버전 관리를 위한 DAO 클래스"""
    
    def __init__(self):
        self.db = Database()
    
    def get_latest_version(self):
        """
        최신 앱 버전 정보를 조회합니다.
        """
        try:
            query = """
            SELECT 
                version_code, 
                version_name, 
                min_api_level, 
                force_update, 
                change_log, 
                created_at
            FROM app_versions 
            ORDER BY version_code DESC 
            LIMIT 1
            """
            
            result = self.db.fetch_one(query)
            
            if result:
                return result
            return None
        except Exception as e:
            logger.error(f"최신 앱 버전 조회 오류: {str(e)}")
            return None
    
    def create_version(self, version_code, version_name, min_api_level=21, force_update=False, change_log=None):
        """
        새 앱 버전 정보를 등록합니다. (관리자 용)
        """
        try:
            query = """
            INSERT INTO app_versions (
                version_code, 
                version_name, 
                min_api_level, 
                force_update, 
                change_log
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                version_code,
                version_name,
                min_api_level,
                force_update,
                change_log
            )
            
            self.db.execute_query(query, params)
            
            return {
                "version_code": version_code,
                "version_name": version_name,
                "min_api_level": min_api_level,
                "force_update": force_update,
                "change_log": change_log
            }
        except Exception as e:
            logger.error(f"앱 버전 등록 오류: {str(e)}")
            return None 