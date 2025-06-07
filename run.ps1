# ── 설정 부분 ──
# 실행할 Python 스크립트 이름 (파일 확장자까지)
$PYTHON_SCRIPT = "main.py"

# 도메인 목록 파일 경로 (Python 스크립트 실행 시 -f 옵션에 전달)
$DOMAIN_FILE = "./domains.txt"

# 몇 줄씩(chunk) 나눠서 실행할지
$CHUNK_SIZE = 10
# ─────────────

# https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt
# domains.txt 파일을 다운로드하는 명령어

curl "https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt" -o $DOMAIN_FILE

# 인자 개수 확인 (2개 또는 3개)
if ($args.Count -lt 2 -or $args.Count -gt 3) {
    Write-Host "Usage: $($MyInvocation.MyCommand.Name) <start_line> <end_line> [skip_header]"
    Write-Host "예시) $($MyInvocation.MyCommand.Name) 10000 11000"
    Write-Host "예시) $($MyInvocation.MyCommand.Name) 10000 11000 True"
    exit 1
}

$START_LINE = [int]$args[0]
$END_LINE = [int]$args[1]
$SKIP_HEADER = if ($args.Count -eq 3) { $args[2] } else { "False" }

# START_LINE부터 END_LINE까지 CHUNK_SIZE 만큼씩 반복
$current = $START_LINE
while ($current -le $END_LINE) {
    # 각 청크 구간의 마지막 줄 계산
    $chunk_end = $current + $CHUNK_SIZE - 1
    if ($chunk_end -gt $END_LINE) {
        $chunk_end = $END_LINE
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] Processing lines $current to $chunk_end..."
    
    # Python 스크립트 실행
    # -f DOMAIN_FILE: 도메인 목록 파일 경로
    # -s current  : 읽기 시작 줄
    # -e chunk_end: 읽기 끝 줄
    # -skh SKIP_HEADER: 헤더 스킵 여부
    uv run $PYTHON_SCRIPT -f $DOMAIN_FILE -s $current -e $chunk_end -skh $SKIP_HEADER

    # 다음 청크의 시작 값 설정
    $current = $chunk_end + 1
}

Write-Host "모든 청크 처리 완료."
