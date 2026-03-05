import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     Transaction:
 *       type: object
 *       required:
 *         - postId
 *         - buyerId
 *         - sellerId
 *         - price
 *       properties:
 *         _id:
 *           type: string
 *           description: 거래 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         postId:
 *           type: string
 *           description: 거래가 이루어진 게시글 ID
 *           example: 65c1b6c2e3f4a123456789aa
 *         buyerId:
 *           type: string
 *           description: 구매자 사용자 ID
 *           example: 65c1b6c2e3f4a123456789bb
 *         sellerId:
 *           type: string
 *           description: 판매자 사용자 ID
 *           example: 65c1b6c2e3f4a123456789cc
 *         price:
 *           type: number
 *           description: 실제 거래 가격
 *           example: 450000
 *         completedAt:
 *           type: string
 *           format: date-time
 *           description: 거래 완료 시간
 *           example: 2026-03-05T12:00:00Z
 */

const transactionSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: "Post", required: true },
  buyerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  price: { type: Number, required: true },
  completedAt: { type: Date, default: Date.now }
});

export default mongoose.model("Transaction", transactionSchema);
