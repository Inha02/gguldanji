# 꿀단지 시드 데이터 스키마 설명

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
