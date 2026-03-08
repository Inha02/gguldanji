import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     ChatRoom:
 *       type: object
 *       required:
 *         - postId
 *         - buyerId
 *         - sellerId
 *       properties:
 *         _id:
 *           type: string
 *           description: 채팅방 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         postId:
 *           type: string
 *           description: 채팅이 이루어지는 게시글 ID
 *           example: 65c1b6c2e3f4a123456789aa
 *         buyerId:
 *           type: string
 *           description: 구매자 사용자 ID
 *           example: 65c1b6c2e3f4a123456789bb
 *         sellerId:
 *           type: string
 *           description: 판매자 사용자 ID
 *           example: 65c1b6c2e3f4a123456789cc
 *         lastMessage:
 *           type: string
 *           description: 마지막 메시지 내용
 *           example: 가격 네고 가능할까요?
 *         createdAt:
 *           type: string
 *           format: date-time
 *           description: 채팅방 생성 시간
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           description: 마지막 업데이트 시간
 *           example: 2026-03-05T12:00:00Z
 */


const chatRoomSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: "Post", required: true },
  buyerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  lastMessage: String
}, { timestamps: true });

export default mongoose.model("ChatRoom", chatRoomSchema);
