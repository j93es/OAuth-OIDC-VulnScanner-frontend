def read_lines_between(filepath: str, start_line: int, end_line: int) -> list[str]:
    """
    파일에서 start_line번 째 줄부터 end_line번 째 줄까지 읽어와 
    각 줄을 요소로 갖는 리스트를 반환하는 함수.

    Parameters:
    ----------
    filepath : str
        읽을 텍스트 파일의 경로
    start_line : int
        읽기 시작할 행 번호 (1부터 시작)
    end_line : int
        읽을 마지막 행 번호 (start_line <= end_line)

    Returns:
    -------
    list[str]
        각 줄을 문자열로 저장한 리스트. 
        파일에 해당 범위의 줄이 없으면 가능한 만큼만 반환.
    """

    if start_line < 1 or end_line < start_line:
        raise ValueError("start_line은 1 이상이어야 하며, end_line은 start_line 이상이어야 합니다.")

    selected_lines: list[str] = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, start=1):
            if idx < start_line:
                # 아직 읽기 시작 전
                continue
            if idx > end_line:
                # 읽을 범위를 벗어났으므로 중단
                break
            # 줄 끝의 개행 문자를 제거하고 리스트에 추가
            selected_lines.append(line.rstrip('\n'))
    return selected_lines
