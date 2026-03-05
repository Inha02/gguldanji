import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     User:
 *       type: object
 *       required:
 *         - nickname
 *       properties:
 *         _id:
 *           type: string
 *           description: 사용자 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         email:
 *           type: string
 *           description: 이메일 (일반 로그인 사용자)
 *           example: inha@test.com
 *         password:
 *           type: string
 *           description: 비밀번호
 *           example: 1234
 *         socialType:
 *           type: string
 *           description: 소셜 로그인 종류
 *           enum:
 *             - kakao
 *             - naver
 *             - null
 *           example: kakao
 *         socialId:
 *           type: string
 *           description: 소셜 로그인 사용자 ID
 *           example: 123456789
 *         nickname:
 *           type: string
 *           description: 사용자 닉네임
 *           example: 곰곰이
 *         gender:
 *           type: string
 *           description: 성별
 *           enum:
 *             - M
 *             - F
 *           example: F
 *         birthDate:
 *           type: string
 *           description: 생년월일 (YYYYMMDD)
 *           example: 20040101
 *         profileImage:
 *           type: string
 *           description: 프로필 이미지 URL
 *           example: https://example.com/profile.jpg
 *         trustScore:
 *           type: number
 *           description: 사용자 신뢰 점수
 *           example: 80
 *         sellerType:
 *           type: string
 *           description: 판매자 성향
 *           example: 친절형
 *         likedCategories:
 *           type: array
 *           description: 관심 카테고리 목록
 *           items:
 *             type: string
 *           example:
 *             - 65c1b6c2e3f4a123456789aa
 *         blockedUsers:
 *           type: array
 *           description: 차단한 사용자 목록
 *           items:
 *             type: string
 *           example:
 *             - 65c1b6c2e3f4a123456789bb
 *         status:
 *           type: string
 *           description: 사용자 상태
 *           enum:
 *             - active
 *             - suspended
 *             - deleted
 *           example: active
 *         createdAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 */

const userSchema = new mongoose.Schema({
  email: { type: String, unique: true, sparse: true },
  password: { type: String },

  socialType: { type: String, enum: ["kakao", "naver", null], default: null },
  socialId: { type: String },

  nickname: { type: String, required: true },
  gender: { type: String, enum: ["M", "F"] },
  birthDate: { type: String }, // YYYYMMDD

  profileImage: String,

  trustScore: { type: Number, default: 0 },
  sellerType: { type: String }, // 친절형 / 무응답형 / 공격형

  likedCategories: [{ type: mongoose.Schema.Types.ObjectId, ref: "Category" }],
  blockedUsers: [{ type: mongoose.Schema.Types.ObjectId, ref: "User" }],

  status: {
    type: String,
    enum: ["active", "suspended", "deleted"],
    default: "active"
  }
}, { timestamps: true });

export default mongoose.model("User", userSchema);
