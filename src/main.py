import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from lib.browser_use.scanner import main_loop
from lib.utils import env_cheker
from lib.utils.progress import progress_file, setup_signal_handler


def setup_environment():
    """환경 변수 로드 및 관련 라이브러리를 초기화합니다."""
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
    else:
        print("⚠️ LMNR_PROJECT_API_KEY 환경 변수가 설정되지 않았습니다. Laminar 기능이 비활성화됩니다.")


def parse_arguments():
    """커맨드 라인 인자를 파싱합니다."""
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
        action="store_true",
        help="HTML 페이지 체크를 건너뛰고 모든 URL을 스캔합니다.",
    )

    return parser.parse_args()


def main():
    """애플리케이션 메인 진입점"""
    setup_environment()
    setup_signal_handler()
    args = parse_arguments()

    # read and remove user data path
    log_file = os.path.join("./data", "userdata.dump")
    if not os.path.exists("./data"):
        os.makedirs("./data")
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            tmp_user_data_dir = f.read().strip()
            try:
                import shutil
                if os.path.exists(tmp_user_data_dir):
                    shutil.rmtree(tmp_user_data_dir)
                    print(f"🔧 이전 실행의 임시 사용자 데이터 디렉토리 {tmp_user_data_dir}를 삭제하였습니다.")
            except (PermissionError, FileNotFoundError, OSError) as e:
                print(f"⚠️ 임시 사용자 데이터 디렉토리 삭제 실패: {e}")
            try:
                os.remove(log_file)
            except OSError:
                pass

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
        print("\n🛑 사용자에 의해 중단되었습니다.")
        # 진행 상황 저장
        from lib.utils.progress import save_progress, request_shutdown
        request_shutdown()
        print("✅ 정리 완료.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 정상 종료 시에만 진행 상황 파일 삭제
        from lib.utils.progress import is_shutdown_requested
        if not is_shutdown_requested() and os.path.exists(progress_file):
            try:
                os.remove(progress_file)
                print("✅ 진행 상황 파일이 삭제되었습니다.")
            except OSError as e:
                print(f"⚠️ 진행 상황 파일 삭제 실패: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
