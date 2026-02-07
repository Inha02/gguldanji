ai-engine/crawler 폴더에서:

1) (원하는 앵커 파일만) 먼저 테스트
python run_all_anchors.py --only 01 --collect 500 --clean 100

2) 문제 없으면 01~16 전체 자동 실행
python run_all_anchors.py --collect 500 --clean 100

3) 수집 끝나면 병합 + 중복 제거
python merge_and_dedupe.py

4) 품질 리포트 생성
python quality_report.py

5) gpt 활용해서 spec_key 뽑기
python run_all_spec_key.py --sample-n 100
→ data/anchors/*.txt 기반으로 카테고리별 spec_key json 생성

6) 게시글별 스펙값 자동추출 + spec_key_hash 생성
python run_all_structuring.py --model gpt-5.1 --reasoning-effort low --skip-existing
→ data/processed/<키워드>/<키워드>_final_100.jsonl 폴더 전부 훑음
→ 각 키워드의 샘플 게시글 몇 개 보고 어느 카테고리인지 자동 분류
→ 그 카테고리 spec_key로 spec_structuring.py 실행
→ data/structured/<category_name>/<keyword>_structured.jsonl 생성
→ *_structured.jsonl = 원본 게시글 + LLM이 뽑은 정규화된 스펙 + 동일스펙 식별자(spec_key_hash)가 합쳐진 최종 ETL 결과