import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     Like:
 *       type: object
 *       required:
 *         - userId
 *         - postId
 *       properties:
 *         _id:
 *           type: string
 *           description: 좋아요 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         userId:
 *           type: string
 *           description: 좋아요를 누른 사용자 ID
 *           example: 65c1b6c2e3f4a123456789aa
 *         postId:
 *           type: string
 *           description: 좋아요 대상 게시글 ID
 *           example: 65c1b6c2e3f4a123456789bb
 *         createdAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 */

const likeSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  postId: { type: mongoose.Schema.Types.ObjectId, ref: "Post", required: true }
}, { timestamps: true });

likeSchema.index({ userId: 1, postId: 1 }, { unique: true });

export default mongoose.model("Like", likeSchema);
