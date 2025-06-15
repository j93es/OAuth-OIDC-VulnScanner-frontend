# ── 설정 부분 ──
# 실행할 Python 스크립트 이름 (파일 확장자까지)
$PYTHON_SCRIPT = "main.py"

# 도메인 목록 파일 경로 (Python 스크립트 실행 시 -f 옵션에 전달)
$DOMAIN_FILE = "./domains.txt"
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

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$timestamp] Processing lines $START_LINE to $END_LINE..."

# Python 스크립트 실행
# -f DOMAIN_FILE: 도메인 목록 파일 경로
# -s START_LINE : 읽기 시작 줄
# -e END_LINE   : 읽기 끝 줄
# -skh SKIP_HEADER: 헤더 스킵 여부
uv run $PYTHON_SCRIPT -f $DOMAIN_FILE -s $START_LINE -e $END_LINE -skh $SKIP_HEADER

Write-Host "처리 완료."
