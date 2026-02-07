ai-engine/crawler 폴더에서:

1) (원하는 앵커 파일만) 먼저 테스트
python run_all_anchors.py --only 01 --collect 500 --clean 100

2) 문제 없으면 01~16 전체 자동 실행
python run_all_anchors.py --collect 500 --clean 100

3) 수집 끝나면 병합 + 중복 제거
python merge_and_dedupe.py

4) 품질 리포트 생성
python quality_report.py

5) gpt 활용해서 카테고리별 spec_key 만들기
python run_all_spec_key.py --sample-n 100
→ data/anchors/*.txt 기반으로 카테고리별 spec_key json 생성

6) 게시글별 스펙값 자동추출 + spec_key_hash 생성
python run_all_structuring.py --model gpt-5.1 --reasoning-effort low --skip-existing
→ data/processed/<키워드>/<키워드>_final_100.jsonl 폴더 전부 훑음
→ 각 키워드의 샘플 게시글 몇 개 보고 어느 카테고리인지 자동 분류
→ 그 카테고리 spec_key로 spec_structuring.py 실행
→ data/structured/<category_name>/<keyword>_structured.jsonl 생성
→ *_structured.jsonl = 원본 게시글 + LLM이 뽑은 정규화된 스펙 + 동일스펙 식별자(spec_key_hash)가 합쳐진 최종 ETL 결과

7) 결과 점검
python check_structured.py

(7-1) make_hash_v2.py : structured를 읽어서 spec_key_hash_v2를 추가 생성(완화 템플릿 적용)
python run_all_hash_v2.py --skip-existing


(7-2) run_all_hash_v2.py : 전체 카테고리/키워드에 대해 위 작업 일괄 실행

8) build_synth_schema.py : spec_key.json을 읽어서 카테고리별 합성용 최소 스키마(6~8개) 자동 생성(+수정용 JSON 저장)
python build_synth_schema.py --target-fields 8


9)
(9-1) synthetic_generate.py : structured_v2를 입력으로 합성데이터 생성(training/demo 모드)
    설계 원칙(너가 원한 것 반영):
    - 입력: data/structured_v2/**/*.jsonl
    - 출력: data/synthetic/<mode>/<category>.csv + <category>.jsonl
    - training 모드: 현실성/일관성 우선(그룹 기반 샘플링)
    - demo 모드: 다양성 조금 더(그룹/카테고리 혼합)

(training 합성 생성)
python run_all_synthetic.py --mode training --hash v2 --n 2000
(demo 합성 생성)
python run_all_synthetic.py --mode demo --hash v2 --n 1000


(9-2) run_all_synthetic.py : 전체 카테고리 일괄 합성 실행


---
품질 레버
1. data/config/hash_v2_templates.json
여기서 v2 해시에 들어갈 필드를 줄이면 → 그룹이 커져서 합성 안정성↑

2. data/config/synth_schema.json
합성 필드를 6~8개로 다이어트하면 → 결측/잡음↓, 현실성↑