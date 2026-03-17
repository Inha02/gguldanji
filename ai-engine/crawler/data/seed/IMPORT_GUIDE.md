# MongoDB 시드 데이터 Import 가이드

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
