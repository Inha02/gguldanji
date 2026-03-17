"""
유저 합성 데이터 생성 + MongoDB 전달용 JSON 패키징
==================================================
게시글 데이터의 sellerId와 매칭되는 유저 데이터를 생성하고,
백엔드 팀에 전달할 MongoDB import용 JSON 파일을 생성한다.

실행:
  python -m crawler.pipeline.generate_users --posts-dir ./crawler/data/posts --output ./crawler/data/seed

출력:
  seed/
  ├── users.json              # 유저 데이터 (MongoDB import용)
  ├── posts.json              # 게시글 데이터 (MongoDB import용)
  ├── categories.json         # 카테고리 데이터 (MongoDB import용)
  ├── SCHEMA.md               # 스키마 설명 문서
  └── IMPORT_GUIDE.md         # MongoDB import 가이드
"""

import argparse
import json
import hashlib
import random
from pathlib import Path
from datetime import datetime, timedelta


# ── 결정론적 ObjectId 생성 ──
def generate_object_id(seed: str) -> str:
    return hashlib.md5(seed.encode()).hexdigest()[:24]


# ── 유저 생성용 데이터 풀 ──
NICKNAMES_PREFIX = [
    "행복한", "즐거운", "신나는", "따뜻한", "귀여운", "멋진", "빛나는", "달콤한",
    "시원한", "깔끔한", "활발한", "조용한", "든든한", "소중한", "예쁜", "착한",
    "용감한", "지혜로운", "상큼한", "포근한", "당당한", "씩씩한", "부지런한", "넉넉한",
    "화사한", "아늑한", "산뜻한", "건강한", "슬기로운", "느긋한",
]

NICKNAMES_SUFFIX = [
    "사과", "바나나", "포도", "딸기", "수박", "참외", "복숭아", "키위",
    "고양이", "강아지", "토끼", "판다", "코알라", "여우", "사슴", "다람쥐",
    "하늘", "바다", "별빛", "구름", "노을", "안개", "무지개", "달빛",
    "마카롱", "커피", "초코", "쿠키", "케이크", "와플", "푸딩", "젤리",
]

EMAIL_DOMAINS = ["gmail.com", "naver.com", "kakao.com", "daum.net", "hanmail.net"]

SOCIAL_TYPES = [None, None, None, "kakao", "kakao", "naver"]  # 50% 일반, 33% 카카오, 17% 네이버

PROFILE_IMAGES = [
    "https://api.dicebear.com/7.x/avataaars/svg?seed={}",
    "https://api.dicebear.com/7.x/big-smile/svg?seed={}",
    "https://api.dicebear.com/7.x/thumbs/svg?seed={}",
    "https://api.dicebear.com/7.x/fun-emoji/svg?seed={}",
]



# 카테고리 목록 (게시글 데이터와 동일)
CATEGORIES = [
    "가구/인테리어", "가전제품", "기타 중고물품", "남성의류", "도서",
    "디지털기기", "반려동물용품", "뷰티/미용", "생활용품", "스포츠/레저",
    "식품", "여성의류", "출산/유아동", "취미/게임", "티켓/교환권", "패션잡화",
]

CATEGORY_IDS = {cat: generate_object_id(f"category:{cat}") for cat in CATEGORIES}


def generate_nickname(idx: int) -> str:
    """결정론적으로 다양한 닉네임 생성"""
    random.seed(idx * 7 + 31)
    prefix = random.choice(NICKNAMES_PREFIX)
    suffix = random.choice(NICKNAMES_SUFFIX)
    num = random.randint(1, 999)
    # 일부는 숫자 없이
    if random.random() < 0.3:
        return f"{prefix}{suffix}"
    return f"{prefix}{suffix}{num}"


def generate_email(idx: int, nickname: str) -> str:
    """이메일 생성"""
    random.seed(idx * 13 + 17)
    domain = random.choice(EMAIL_DOMAINS)
    clean = nickname.replace(" ", "").lower()
    num = random.randint(1, 9999)
    return f"{clean}{num}@{domain}"


def generate_user(idx: int, seller_id: str) -> dict:
    """유저 1명 생성"""
    random.seed(idx * 11 + 42)

    nickname = generate_nickname(idx)
    email = generate_email(idx, nickname)
    social_type = random.choice(SOCIAL_TYPES)

    # 생년월일: 1975~2005 사이
    birth_year = random.randint(1975, 2005)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = f"{birth_year}{birth_month:02d}{birth_day:02d}"

    # 가입일: 2024-01-01 ~ 2026-02-28 사이
    join_offset = random.randint(0, 780)
    joined_at = datetime(2024, 1, 1) + timedelta(days=join_offset)

    # 관심 카테고리: 1~4개 랜덤
    num_liked = random.randint(1, 4)
    liked_cats = random.sample(CATEGORIES, num_liked)
    liked_cat_ids = [CATEGORY_IDS[c] for c in liked_cats]

    # 신뢰도: 30~100 사이 (대부분 60~90)
    trust_score = min(100, max(30, int(random.gauss(75, 15))))

    # 프로필 이미지
    img_template = random.choice(PROFILE_IMAGES)
    profile_image = img_template.format(seller_id[:8])

    user = {
        "_id": seller_id,
        "email": email,
        "password": "$2b$10$dummyhashvalue" + seller_id[:20],  # 더미 bcrypt
        "socialType": social_type,
        "socialId": f"{social_type}_{seller_id[:16]}" if social_type else None,
        "nickname": nickname,
        "gender": random.choice(["M", "F"]),
        "birthDate": birth_date,
        "profileImage": profile_image,
        "joinedAt": joined_at.isoformat(),
        "trustScore": trust_score,
        "likedCategories": liked_cat_ids,
        "blockedUsers": [],
        "status": "active",
        "createdAt": joined_at.isoformat(),
        "updatedAt": joined_at.isoformat(),
    }

    return user


def generate_schema_doc(output_dir: Path):
    """스키마 설명 문서 생성"""
    doc = """# 꿀단지 시드 데이터 스키마 설명

## 1. users 컬렉션

| 필드 | 타입 | 설명 |
|------|------|------|
| _id | ObjectId (String) | 유저 고유 ID, posts.sellerId와 매칭 |
| email | String | 이메일 (합성) |
| password | String | bcrypt 해시 (더미값, 실제 로그인 불가) |
| socialType | String / null | "kakao" / "naver" / null |
| socialId | String / null | 소셜 로그인 고유 ID |
| nickname | String | 닉네임 (합성) |
| gender | String | "M" / "F" |
| birthDate | String | YYYYMMDD 형식 |
| profileImage | String | 프로필 이미지 URL (DiceBear 아바타) |
| joinedAt | Date | 가입일 |
| trustScore | Number | 신뢰도 (30~100) |
| likedCategories | [ObjectId] | 온보딩 관심 카테고리 ID 배열 |
| blockedUsers | [ObjectId] | 차단 유저 (초기값: 빈 배열) |
| status | String | "active" / "suspended" / "deleted" |
| createdAt | Date | 생성일 |
| updatedAt | Date | 수정일 |

> **참고**: 판매자 성향(sellerType) 필드는 users에 넣지 않습니다. 별도 seller_profiles 컬렉션에서 관리됩니다.

## 2. posts 컬렉션

| 필드 | 타입 | 설명 |
|------|------|------|
| _id | ObjectId (String) | 게시글 고유 ID |
| sellerId | ObjectId (String) | users._id 참조 |
| title | String | 게시글 제목 (LLM 생성) |
| description | String | 게시글 설명 (LLM 생성) |
| images | [String] | 이미지 경로 배열 |
| imageCount | Number | 이미지 수 (1 또는 2) |
| categoryId | ObjectId (String) | categories._id 참조 |
| category | String | 카테고리명 (역정규화) |
| price | Number | 판매 가격 (원) |
| isFree | Boolean | 무료 나눔 여부 |
| condition | String | "S급" / "A급" / "B급" / "C급" / "부품용" |
| sensitiveAttributes | Object | 카테고리별 상세 속성 (브랜드, 모델명 등) |
| options | Object | 옵션 (아래 참조) |
| options.hasBox | Boolean | 정품박스 유무 |
| options.hasAccessories | Boolean | 부속품 유무 |
| options.hasDefects | Boolean | 하자 유무 |
| options.isNegotiable | Boolean | 네고 가능 여부 |
| options.usagePeriodMonths | Number / null | 사용 기간 (개월) |
| aiPriceMin | Number / null | AI 추정 최저가 (가격 가이드 에이전트가 채움) |
| aiPriceMax | Number / null | AI 추정 최고가 |
| aiPriceReason | String / null | AI 추정 근거 |
| location | Object | {address, lat, lng} |
| status | String | "selling" / "reserved" / "sold" |
| viewCount | Number | 조회수 |
| likeCount | Number | 찜수 |
| createdAt | Date | 등록일 |
| updatedAt | Date | 수정일 |

## 3. categories 컬렉션

| 필드 | 타입 | 설명 |
|------|------|------|
| _id | ObjectId (String) | 카테고리 고유 ID |
| name | String | 카테고리명 |
| recommended | [String] | 권장 입력 속성 |
| optional | [String] | 선택 입력 속성 |

## 4. seller_profiles 컬렉션 (AI 엔진이 자동 생성)

| 필드 | 타입 | 설명 |
|------|------|------|
| _id | ObjectId | 자동 생성 |
| sellerId | ObjectId (String) | users._id 참조 |
| profile | Object | AI 성향 분석 프로필 전체 JSON (아래 참조) |
| lastAnalyzedAt | Date | 마지막 분석 시각 |
| totalMessagesAnalyzed | Number | 분석에 사용된 총 메시지 수 |
| createdAt | Date | 최초 생성일 |
| updatedAt | Date | 수정일 |

### profile 필드 구조

```json
{
  "profile_version": 2,
  "analysis_summary": "가격 민감도가 높고 효율적 거래를 선호하는 판매자입니다.",
  "dimensions": {
    "transaction_motivation": {
      "price_sensitivity": {"score": 4, "confidence": 0.85, "evidence": ["..."]},
      "efficiency_orientation": {"score": 5, "confidence": 0.90, "evidence": ["..."]},
      "enjoyment_orientation": {"score": 1, "confidence": 0.50, "evidence": []},
      "negotiation_flexibility": {"score": 3, "confidence": 0.75, "evidence": ["..."]}
    },
    "communication_style": {
      "response_pattern": {"score": 5, ...},
      "information_proactivity": {"score": 4, ...},
      "tone_friendliness": {"score": 3, ...},
      "clarity_structure": {"score": 5, ...}
    },
    "trust_building": {
      "product_description_detail": {"score": 4, ...},
      "transaction_transparency": {"score": 5, ...},
      "issue_handling_attitude": {"score": 3, ...}
    }
  },
  "change_history": [...]
}
```

> **참고**: 시드 데이터에는 seller_profiles가 비어 있습니다.  
> 채팅 데이터가 10건 이상 쌓이면 AI 판매자 성향 분석 에이전트가 자동으로 프로필을 생성합니다.  
> API: `POST /api/v1/profiling/analyze`

## 관계도

```
users._id ←──── posts.sellerId
users._id ←──── seller_profiles.sellerId
categories._id ←──── posts.categoryId
categories._id ←──── users.likedCategories[]
```
"""
    with open(output_dir / "SCHEMA.md", "w", encoding="utf-8") as f:
        f.write(doc)


def generate_import_guide(output_dir: Path):
    """MongoDB import 가이드 생성"""
    guide = """# MongoDB 시드 데이터 Import 가이드

## 파일 목록

| 파일 | 컬렉션 | 건수 | 설명 |
|------|--------|------|------|
| users.json | users | 200명 | 합성 유저 데이터 |
| posts.json | posts | ~19,000건 | 게시글 데이터 (이미지 포함) |
| categories.json | categories | 16건 | 카테고리 마스터 |

> **참고**: seller_profiles 컬렉션은 시드 데이터에 포함되지 않습니다.
> 채팅 데이터가 쌓이면 AI 에이전트가 자동으로 생성합니다.
> 빈 컬렉션만 미리 만들어두면 됩니다.

## Import 방법

### 방법 1: mongoimport (권장)

```bash
# 1. MongoDB 실행 확인
mongosh --eval "db.runCommand({ping:1})"

# 2. 데이터 Import
mongoimport --db gguldanji --collection users --file users.json --jsonArray --drop
mongoimport --db gguldanji --collection posts --file posts.json --jsonArray --drop
mongoimport --db gguldanji --collection categories --file categories.json --jsonArray --drop

# 3. seller_profiles 빈 컬렉션 생성 + 인덱스
mongosh gguldanji --eval '
  db.createCollection("seller_profiles");
  db.seller_profiles.createIndex({sellerId: 1}, {unique: true});
  db.posts.createIndex({sellerId: 1});
  db.posts.createIndex({categoryId: 1});
  db.posts.createIndex({status: 1, createdAt: -1});
  db.users.createIndex({email: 1}, {unique: true});
  db.users.createIndex({nickname: 1});
'
```

### 방법 2: Node.js 스크립트

```javascript
const mongoose = require('mongoose');
const fs = require('fs');

async function seed() {
  await mongoose.connect('mongodb://localhost:27017/gguldanji');
  
  const users = JSON.parse(fs.readFileSync('users.json', 'utf-8'));
  const posts = JSON.parse(fs.readFileSync('posts.json', 'utf-8'));
  const categories = JSON.parse(fs.readFileSync('categories.json', 'utf-8'));

  await mongoose.connection.db.collection('users').drop().catch(() => {});
  await mongoose.connection.db.collection('posts').drop().catch(() => {});
  await mongoose.connection.db.collection('categories').drop().catch(() => {});
  await mongoose.connection.db.collection('seller_profiles').drop().catch(() => {});

  await mongoose.connection.db.collection('users').insertMany(users);
  await mongoose.connection.db.collection('posts').insertMany(posts);
  await mongoose.connection.db.collection('categories').insertMany(categories);

  // seller_profiles 인덱스 생성
  await mongoose.connection.db.collection('seller_profiles').createIndex({sellerId: 1}, {unique: true});

  console.log(`users: ${users.length}, posts: ${posts.length}, categories: ${categories.length}`);
  console.log('seller_profiles: 빈 컬렉션 생성 (AI 에이전트가 자동 채움)');
  await mongoose.disconnect();
}

seed();
```

## 주의사항

- _id는 24자리 hex 문자열입니다. MongoDB ObjectId로 자동 변환되지 않으므로, 필요 시 `new ObjectId(id)` 로 변환하세요.
- password는 더미 해시값입니다. 실제 로그인 테스트 시 별도 비밀번호 설정이 필요합니다.
- images 경로는 상대경로(`images/카테고리/파일명.png`)입니다. 서버에서 서빙할 base URL을 앞에 붙여야 합니다.
- aiPriceMin/Max/Reason은 null입니다. 가격 가이드 에이전트가 실행되면 자동으로 채워집니다.
"""
    with open(output_dir / "IMPORT_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)


# 카테고리별 속성 스키마 (schemas.py에서 가져옴)
CATEGORY_SCHEMA = {
    "디지털기기": {"recommended": ["브랜드", "모델명"], "optional": ["저장용량", "색상", "출시년도", "RAM", "화면크기", "배터리성능"]},
    "가전제품": {"recommended": ["브랜드", "모델명"], "optional": ["종류", "용량_리터", "용량_kg", "도어타입", "설치여부"]},
    "패션잡화": {"recommended": ["브랜드"], "optional": ["모델명", "종류", "소재", "색상", "정품인증여부"]},
    "남성의류": {"recommended": ["브랜드"], "optional": ["사이즈", "시즌", "소재", "착용횟수", "색상"]},
    "여성의류": {"recommended": ["브랜드"], "optional": ["사이즈", "시즌", "소재", "착용횟수", "색상", "기장"]},
    "스포츠/레저": {"recommended": ["브랜드"], "optional": ["모델명", "종류", "샤프트종류", "세트구성"]},
    "출산/유아동": {"recommended": ["브랜드"], "optional": ["모델명", "종류", "사용개월수"]},
    "취미/게임": {"recommended": [], "optional": ["모델명", "동봉게임수"]},
    "뷰티/미용": {"recommended": ["브랜드"], "optional": ["모델명", "종류", "제품명", "용량_ml", "잔량_퍼센트", "개봉여부"]},
    "반려동물용품": {"recommended": [], "optional": ["브랜드", "종류", "소재", "크기", "대상동물크기"]},
    "생활용품": {"recommended": [], "optional": ["브랜드", "종류", "소재", "크기", "칸수", "색상", "조립여부"]},
    "가구/인테리어": {"recommended": [], "optional": ["브랜드", "종류", "소재", "색상", "조립여부", "용도"]},
    "도서": {"recommended": [], "optional": ["출판사", "종류", "과목구성", "세트구성", "필기여부", "발행년도"]},
    "식품": {"recommended": [], "optional": ["브랜드", "제품명", "용량", "유통기한", "형태", "개봉여부"]},
    "티켓/교환권": {"recommended": ["종류"], "optional": ["사용처", "권종금액", "매수", "유효기한", "이벤트명", "날짜", "좌석등급"]},
    "기타 중고물품": {"recommended": [], "optional": ["브랜드", "종류", "사용횟수"]},
}


def main():
    parser = argparse.ArgumentParser(description="유저 데이터 생성 + MongoDB 시드 패키징")
    parser.add_argument("--posts-dir", type=str, required=True, help="posts/ 디렉토리 경로")
    parser.add_argument("--output", type=str, required=True, help="출력 디렉토리 (seed/)")
    args = parser.parse_args()

    posts_dir = Path(args.posts_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("유저 데이터 생성 + MongoDB 시드 패키징")
    print("=" * 60)

    # ── 1. 게시글에서 sellerId 추출 ──
    print("\n[1/5] 게시글 데이터 로드 중...")
    all_posts = []
    seller_ids = set()

    posts_all_path = posts_dir / "posts_all.jsonl"
    if not posts_all_path.exists():
        print(f"ERROR: {posts_all_path} 파일이 없습니다.")
        return

    with open(posts_all_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                post = json.loads(line)
                all_posts.append(post)
                seller_ids.add(post["sellerId"])

    print(f"  게시글: {len(all_posts):,}건")
    print(f"  판매자: {len(seller_ids)}명")

    # ── 2. 유저 데이터 생성 ──
    print("\n[2/5] 유저 데이터 생성 중...")
    seller_id_list = sorted(seller_ids)
    users = []
    for idx, sid in enumerate(seller_id_list):
        user = generate_user(idx, sid)
        users.append(user)

    print(f"  유저 {len(users)}명 생성 완료")

    # 통계
    gender_dist = {}
    social_dist = {}
    for u in users:
        gender_dist[u["gender"]] = gender_dist.get(u["gender"], 0) + 1
        st = u["socialType"] or "일반"
        social_dist[st] = social_dist.get(st, 0) + 1

    print(f"  성별: {gender_dist}")
    print(f"  로그인: {social_dist}")

    # ── 3. 카테고리 데이터 생성 ──
    print("\n[3/5] 카테고리 데이터 생성 중...")
    categories = []
    for cat_name, schema in CATEGORY_SCHEMA.items():
        categories.append({
            "_id": CATEGORY_IDS[cat_name],
            "name": cat_name,
            "recommended": schema["recommended"],
            "optional": schema["optional"],
        })
    print(f"  카테고리 {len(categories)}개 생성 완료")

    # ── 4. JSON 파일 저장 ──
    print("\n[4/5] JSON 파일 저장 중...")

    # users.json
    users_path = output_dir / "users.json"
    with open(users_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    print(f"  {users_path} ({len(users)}건)")

    # posts.json (JSONL → JSON Array)
    posts_path = output_dir / "posts.json"
    with open(posts_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False)
    print(f"  {posts_path} ({len(all_posts):,}건)")

    # categories.json
    cat_path = output_dir / "categories.json"
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f"  {cat_path} ({len(categories)}건)")

    # ── 5. 문서 생성 ──
    print("\n[5/5] 문서 생성 중...")
    generate_schema_doc(output_dir)
    print(f"  {output_dir / 'SCHEMA.md'}")
    generate_import_guide(output_dir)
    print(f"  {output_dir / 'IMPORT_GUIDE.md'}")

    # ── 요약 ──
    print(f"\n{'=' * 60}")
    print(f"완료! 출력 디렉토리: {output_dir}")
    print(f"{'=' * 60}")
    print(f"  users.json        — {len(users)}명")
    print(f"  posts.json        — {len(all_posts):,}건")
    print(f"  categories.json   — {len(categories)}개")
    print(f"  SCHEMA.md         — 스키마 설명")
    print(f"  IMPORT_GUIDE.md   — MongoDB import 가이드")
    print(f"\n백엔드 팀에 seed/ 폴더를 통째로 전달하세요.")


if __name__ == "__main__":
    main()