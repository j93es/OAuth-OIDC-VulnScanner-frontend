import asyncio
import csv
import os

from lib.browser_use.agents import (
    extract_oauth_list,
    get_retry_queue_status,
    start_retry_queue_processor,
    test_oauth_login,
)
from lib.browser_use.cleanup import cleanup_browser_resources
from lib.utils import is_html_url, notify_backend, read_lines_between
from lib.utils.progress import (
    current_progress,
    is_shutdown_requested,
    load_progress,
    progress_file,
    save_progress,
)


async def scan_one_url(url: str, skip_html_check: bool = False):
    """URL 스캔 통합 함수: OAuth 리스트 추출 → 개별 OAuth 로그인 시도"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🚀 스캔 시작: {target_url}")

    # Backend에 스캔 시작을 알림
    notify_backend(target_url)

    # 1) URL이 HTML 페이지인지 확인
    if not is_html_url(target_url) and not skip_html_check:
        print(f"❌ {target_url} 은(는) HTML이 아닙니다. 스킵합니다.")
        return

    # 1단계: OAuth 리스트 추출
    oauth_entries = await extract_oauth_list(target_url)

    if not oauth_entries:
        print(f"❌ {target_url}에서 OAuth 제공자를 찾을 수 없습니다.")
        return

    print("-" * 50)
    print(f"🔗 스캔 URL: {url}")
    print(f"🔐 발견된 OAuth 제공자들: {len(oauth_entries)}개")
    for entry in oauth_entries:
        print(f"  - {entry}")
    print("-" * 50)

    # CSV에 OAuth 리스트 저장
    csv_file = "./data/oauth_providers.csv"
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["issuer", "provider", "oauth_uri", "login_tested"])
        for entry in oauth_entries:
            writer.writerow([url, entry, "", "pending"])

    # 2단계: 각 OAuth 제공자별로 개별 로그인 시도
    for i, oauth_entry in enumerate(oauth_entries):
        print(f"\n🔄 OAuth 로그인 테스트 {i+1}/{len(oauth_entries)}: {oauth_entry}")

        # OAuth 간 대기 시간
        if i > 0:
            print("⏳ OAuth 테스트 간 대기 중 (30초)...")
            await asyncio.sleep(30)

        # 개별 OAuth 로그인 시도
        success = await test_oauth_login(url, oauth_entry)

        # 결과를 CSV에 업데이트 (간단하게 로그만 남김)
        status = "success" if success else "failed"
        print(f"📝 {oauth_entry} 로그인 결과: {status}")


async def main_loop(
    filepath: str, start_line: int, end_line: int, skip_html_check: bool = False
):
    """지정된 URL 목록에 대해 스캔을 실행하는 메인 루프"""
    try:
        # 재시도 큐 처리기 시작
        await start_retry_queue_processor()

        target_list = read_lines_between(
            filepath=filepath, start_line=start_line, end_line=end_line
        )

        # 전체 목록 길이를 저장 (재개 시에도 유지되어야 함)
        total_count = len(target_list)
        current_progress["total"] = total_count
        current_progress["start_line"] = start_line
        current_progress["current_index"] = 0

        prev_progress = load_progress()
        if prev_progress and prev_progress.get("start_line") == start_line:
            print("📋 이전 진행 상황을 발견했습니다:")
            print(
                f"   - 이전 완료: {prev_progress['current_index']}/{prev_progress['total']}"
            )
            print(f"   - 마지막 처리: {prev_progress.get('current_url', 'N/A')}")

            resume = input("이어서 진행하시겠습니까? (y/n): ").lower().strip()
            if resume == "y":
                start_index = prev_progress.get("current_index", 0)
                current_progress["current_index"] = start_index
                # 전체 개수는 원래 목록 길이로 유지
                current_progress["total"] = total_count
                target_list = target_list[start_index:]
                print(f"✅ {start_index}번째부터 재개합니다.")

        for i, url in enumerate(target_list):
            # 종료 요청 체크
            if is_shutdown_requested():
                print("🛑 종료 요청으로 인해 스캔을 중단합니다.")
                break
                
            # current_index는 전체 목록에서의 현재 위치를 나타냄
            current_url_index = current_progress["current_index"]
            current_progress["current_url"] = url

            print(
                f"\n🔄 Processing {current_url_index + 1}/{current_progress['total']}: {url}"
            )
            print(
                f"📍 {os.path.basename(filepath)}의 {start_line + current_url_index}번째 줄"
            )

            # 재시도 큐 상태 확인 및 출력
            retry_status = await get_retry_queue_status()
            if retry_status["queue_length"] > 0:
                print(f"⏳ 재시도 큐에 {retry_status['queue_length']}개 작업 대기 중")

            if i > 0:
                print("⏳ API 쿼터 보호를 위해 30초 대기 중...")
                # 대기 중에도 종료 요청 체크
                for _ in range(30):
                    if is_shutdown_requested():
                        print("🛑 대기 중 종료 요청으로 스캔을 중단합니다.")
                        return
                    await asyncio.sleep(1)

            try:
                await scan_one_url(url, skip_html_check=skip_html_check)
            except Exception as e:
                print(f"❌ {url} 스캔 중 오류 발생: {e}")
                continue

            # 스캔 완료 후 재시도 큐 상태 확인
            retry_status_after = await get_retry_queue_status()
            if retry_status_after["queue_length"] > 0:
                print(
                    f"📊 스캔 완료 후 재시도 큐 상태: {retry_status_after['queue_length']}개 작업 대기 중"
                )

            # 다음 URL로 진행
            current_progress["current_index"] = current_url_index + 1
            save_progress()

        # 모든 URL 처리 완료 후 재시도 큐가 빌 때까지 대기
        if not is_shutdown_requested():
            print("\n🔄 모든 URL 처리 완료. 재시도 큐 처리 대기 중...")
            while True:
                if is_shutdown_requested():
                    print("🛑 재시도 큐 대기 중 종료 요청으로 중단합니다.")
                    break
                    
                retry_status = await get_retry_queue_status()
                if retry_status["queue_length"] == 0:
                    break
                print(
                    f"⏳ 재시도 큐에 {retry_status['queue_length']}개 작업 남음. 30초 후 다시 확인..."
                )
                # 대기 중에도 종료 요청 체크
                for _ in range(30):
                    if is_shutdown_requested():
                        print("🛑 재시도 큐 대기 중 종료 요청으로 중단합니다.")
                        break
                    await asyncio.sleep(1)

            if not is_shutdown_requested():
                print(f"\n🎉 모든 스캔이 완료되었습니다! ({total_count}개 URL)")
                print("🎉 재시도 큐도 모두 처리되었습니다!")
            else:
                print("\n🛑 종료 요청으로 인해 스캔이 중단되었습니다.")
        else:
            print("\n🛑 종료 요청으로 인해 스캔이 중단되었습니다.")
            
    finally:
        # 항상 리소스 정리
        print("🔄 브라우저 리소스를 정리합니다...")
        await cleanup_browser_resources()
