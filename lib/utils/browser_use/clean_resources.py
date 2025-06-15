from pathlib import Path

async def clean_resources(agent=None, session=None):
    """리소스를 정리하는 함수"""
    storage_state_temp_path = Path("./data/storage_state_temp.json").resolve()
    if storage_state_temp_path.exists():
        try:
            # remove file
            print(f"🗑️ 임시 스토리지 상태 파일 삭제 중: {storage_state_temp_path}")
            # unlink removes the file
            storage_state_temp_path.unlink()
            print("🗑️ 임시 스토리지 상태 파일 삭제 완료.")
        except Exception as e:
            print(f"⚠️ 임시 스토리지 상태 파일 삭제 실패: {e}")

    if agent:
        try:
            await agent.close()
        except Exception as e:
            print(f"⚠️ 에이전트 리소스 정리 실패: {e}")
    if session:
        try:
            await session.close()
        except Exception as e:
            print(f"⚠️ 세션 리소스 정리 실패: {e}")
