import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     Post:
 *       type: object
 *       required:
 *         - sellerId
 *         - title
 *       properties:
 *         _id:
 *           type: string
 *           example: "65f1a2c3b4d5e6"
 *         sellerId:
 *           type: string
 *           description: 판매자 User ID
 *           example: "65f1a2c3b4d5e6"
 *         title:
 *           type: string
 *           example: "아이폰 13"
 *         description:
 *           type: string
 *           example: "사용감 약간 있음"
 *         images:
 *           type: array
 *           items:
 *             type: string
 *           example:
 *             - "https://image.com/1.jpg"
 *             - "https://image.com/2.jpg"
 *         categoryId:
 *           type: string
 *           description: 카테고리 ID
 *           example: "65f1a2c3b4d5e6"
 *         price:
 *           type: number
 *           example: 550000
 *         isFree:
 *           type: boolean
 *           example: false
 *         aiPriceMin:
 *           type: number
 *           example: 500000
 *         aiPriceMax:
 *           type: number
 *           example: 600000
 *         aiPriceReason:
 *           type: string
 *           example: "최근 거래 평균 가격 기반"
 *         location:
 *           type: object
 *           properties:
 *             address:
 *               type: string
 *               example: "서울시 용산구"
 *             lat:
 *               type: number
 *               example: 37.5326
 *             lng:
 *               type: number
 *               example: 126.9906
 *         status:
 *           type: string
 *           enum:
 *             - selling
 *             - reserved
 *             - sold
 *           example: selling
 *         viewCount:
 *           type: number
 *           example: 10
 *         likeCount:
 *           type: number
 *           example: 3
 *         createdAt:
 *           type: string
 *           format: date-time
 *           example: "2026-03-05T12:00:00.000Z"
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           example: "2026-03-05T12:00:00.000Z"
 */

const postSchema = new mongoose.Schema({
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  title: { type: String, required: true },
  description: String,
  images: [String],

  categoryId: { type: mongoose.Schema.Types.ObjectId, ref: "Category" },

  price: Number,
  isFree: { type: Boolean, default: false },

  aiPriceMin: Number,
  aiPriceMax: Number,
  aiPriceReason: String,

  location: {
    address: String,
    lat: Number,
    lng: Number
  },

  status: {
    type: String,
    enum: ["selling", "reserved", "sold"],
    default: "selling"
  },

  viewCount: { type: Number, default: 0 },
  likeCount: { type: Number, default: 0 }

}, { timestamps: true });

export default mongoose.model("Post", postSchema);
