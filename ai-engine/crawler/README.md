ai-engine/crawler 폴더에서:

1) (원하는 앵커 파일만) 먼저 테스트
python run_all_anchors.py --only 01 --collect 500 --clean 100

2) 문제 없으면 01~16 전체 자동 실행
python run_all_anchors.py --collect 500 --clean 100

3) 수집 끝나면 병합 + 중복 제거
python merge_and_dedupe.py

4) 품질 리포트 생성
python quality_report.py