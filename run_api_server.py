#!/usr/bin/env python
"""
건강 관리 AI API 서버 실행 스크립트
"""

import os
import sys
import argparse
import logging
import uvicorn
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_server.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(description="Health AI API 서버 실행")
    parser.add_argument(
        "--host", 
        type=str, 
        default=os.environ.get("API_HOST", "0.0.0.0"),
        help="서버 호스트 주소 (기본값: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.environ.get("API_PORT", 8080)),
        help="서버 포트 (기본값: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="코드 변경 시 자동 재시작 활성화"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    return parser.parse_args()

def main():
    """서버 시작 함수"""
    args = parse_args()
    
    # 디버그 모드인 경우 로그 레벨 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("디버그 모드가 활성화되었습니다.")
    
    # 서버 시작 로그
    logger.info(f"Health AI API 서버를 {args.host}:{args.port}에서 시작합니다...")
    
    # Uvicorn으로 FastAPI 서버 실행
    uvicorn.run(
        "app.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("서버가 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)