import asyncio
import argparse
import os
from dotenv import load_dotenv

from lib.utils import env_cheker
from lib.browser_use.scanner import main_loop
from lib.utils.progress import setup_signal_handler, progress_file

# .env 파일 로드
load_dotenv(verbose=True, override=True)

# 환경 변수 체크
env_cheker()

# Laminar 초기화 (선택적)
if os.getenv("LMNR_PROJECT_API_KEY"):
    try:
        from lmnr import Laminar
        Laminar.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))
    except ImportError:
        print("⚠️ Laminar 라이브러리가 설치되지 않았습니다. 관련 기능이 비활성화됩니다.")


def main():
    """애플리케이션 메인 진입점"""
    # 시그널 핸들러 설정
    setup_signal_handler()

    parser = argparse.ArgumentParser(
        prog="domain_scanner",
        description="도메인 목록 파일에서 지정한 줄 범위를 읽어 SSO 스캔을 수행합니다.",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="도메인 목록이 들어 있는 텍스트 파일 경로 (예: ./domains.txt)",
    )
    parser.add_argument(
        "-s", "--start", type=int, required=True, help="읽기 시작 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-e", "--end", type=int, required=True, help="읽기 종료 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-skh",
        "--skip-html-check",
        action='store_true', # 플래그 형식으로 변경
        help="HTML 페이지 체크를 건너뛰고 모든 URL을 스캔합니다.",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            main_loop(
                filepath=args.file,
                start_line=args.start,
                end_line=args.end,
                skip_html_check=args.skip_html_check,
            )
        )
    except KeyboardInterrupt:
        # signal_handler가 처리하므로 여기서는 별도 처리 불필요
        pass
    finally:
        # 정상 종료 시 진행 상황 파일 삭제
        if os.path.exists(progress_file):
            try:
                os.remove(progress_file)
            except OSError as e:
                print(f"오류: 진행 상황 파일을 삭제하지 못했습니다. {e}")


if __name__ == "__main__":
    main()