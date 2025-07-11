"""
브라우저 리소스 정리를 위한 모듈
"""
import os
import shutil
import asyncio
from pathlib import Path


async def cleanup_browser_resources(agent=None, session=None, user_data_dir=None):
    """브라우저 관련 리소스를 정리하는 함수"""
    print("🔄 브라우저 리소스 정리를 시작합니다...")
    
    # 에이전트 리소스 정리
    if agent:
        try:
            print("� 에이전트 리소스 정리 중...")
            # 브라우저 종료 대기 시간 설정
            await asyncio.wait_for(agent.close(), timeout=10.0)
            print("✅ 에이전트 리소스 정리 완료.")
        except asyncio.TimeoutError:
            print("⚠️ 에이전트 종료 시간 초과. 강제 종료합니다.")
        except Exception as e:
            print(f"⚠️ 에이전트 리소스 정리 실패: {e}")

    # 세션 리소스 정리
    if session:
        try:
            print("🔄 세션 리소스 정리 중...")
            await asyncio.wait_for(session.close(), timeout=5.0)
            print("✅ 세션 리소스 정리 완료.")
        except asyncio.TimeoutError:
            print("⚠️ 세션 종료 시간 초과.")
        except Exception as e:
            print(f"⚠️ 세션 리소스 정리 실패: {e}")

    # 임시 스토리지 상태 파일 삭제
    storage_state_temp_path = Path("./data/storage_state_temp.json").resolve()
    if storage_state_temp_path.exists():
        try:
            print(f"�️ 임시 스토리지 상태 파일 삭제 중: {storage_state_temp_path}")
            storage_state_temp_path.unlink()
            print("✅ 임시 스토리지 상태 파일 삭제 완료.")
        except Exception as e:
            print(f"⚠️ 임시 스토리지 상태 파일 삭제 실패: {e}")

    # 임시 사용자 데이터 디렉토리 정리
    if user_data_dir and os.path.exists(user_data_dir):
        try:
            print(f"🗑️ 임시 사용자 데이터 디렉토리 삭제 중: {user_data_dir}")
            await asyncio.sleep(0.5)  # 브라우저가 완전히 종료될 시간 제공
            shutil.rmtree(user_data_dir)
            print("✅ 임시 사용자 데이터 디렉토리 삭제 완료.")
        except Exception as e:
            print(f"⚠️ 임시 사용자 데이터 디렉토리 삭제 실패: {e}")

    # userdata.dump 파일에서 기록된 디렉토리 정리
    log_file = "./data/userdata.dump"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                tmp_user_data_dir = f.read().strip()
                if tmp_user_data_dir and os.path.exists(tmp_user_data_dir):
                    print(f"🗑️ 기록된 임시 사용자 데이터 디렉토리 삭제 중: {tmp_user_data_dir}")
                    await asyncio.sleep(0.5)  # 브라우저가 완전히 종료될 시간 제공
                    shutil.rmtree(tmp_user_data_dir)
                    print("✅ 기록된 임시 사용자 데이터 디렉토리 삭제 완료.")
            os.remove(log_file)
            print("✅ userdata.dump 파일 삭제 완료.")
        except Exception as e:
            print(f"⚠️ userdata.dump 관련 정리 실패: {e}")
    
    print("✅ 브라우저 리소스 정리가 완료되었습니다.")


def cleanup_all_running_tasks():
    """실행 중인 모든 asyncio 태스크를 정리"""
    try:
        loop = asyncio.get_running_loop()
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        
        if tasks:
            print(f"🔄 {len(tasks)}개의 실행 중인 태스크를 정리합니다...")
            for task in tasks:
                task.cancel()
            
            # 태스크들이 정리될 때까지 잠시 대기
            async def wait_for_tasks():
                await asyncio.gather(*tasks, return_exceptions=True)
            
            asyncio.create_task(wait_for_tasks())
            print("✅ 모든 태스크 정리 완료.")
    except RuntimeError:
        # 이벤트 루프가 실행 중이 아닌 경우
        pass
    except Exception as e:
        print(f"⚠️ 태스크 정리 중 오류: {e}")


async def emergency_cleanup():
    """긴급 종료 시 최소한의 리소스 정리"""
    print("🚨 긴급 리소스 정리 실행 중...")
    
    # 모든 태스크 취소
    cleanup_all_running_tasks()
    
    # 기본 리소스 정리
    await cleanup_browser_resources()
    
    print("✅ 긴급 리소스 정리 완료.")
