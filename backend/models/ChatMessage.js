import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     ChatMessage:
 *       type: object
 *       required:
 *         - roomId
 *         - senderId
 *       properties:
 *         _id:
 *           type: string
 *           description: 채팅 메시지 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         roomId:
 *           type: string
 *           description: 채팅방 ID
 *           example: 65c1b6c2e3f4a123456789aa
 *         senderId:
 *           type: string
 *           description: 메시지를 보낸 사용자 ID
 *           example: 65c1b6c2e3f4a123456789bb
 *         content:
 *           type: string
 *           description: 메시지 내용
 *           example: 가격 네고 가능할까요?
 *         image:
 *           type: string
 *           description: 채팅 이미지 URL
 *           example: https://example.com/chat-image.jpg
 *         aiSuggestion:
 *           type: array
 *           description: AI 추천 답변 목록
 *           items:
 *             type: string
 *           example:
 *             - 조금은 가능합니다 🙂
 *             - 죄송하지만 어렵습니다 🙏
 *         isBadManner:
 *           type: boolean
 *           description: 비매너 발언 여부
 *           example: false
 *         readBy:
 *           type: array
 *           description: 메시지를 읽은 사용자 ID 목록
 *           items:
 *             type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *           description: 메시지 생성 시간
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           description: 메시지 수정 시간
 *           example: 2026-03-05T12:00:00Z
 */

const chatMessageSchema = new mongoose.Schema({
  roomId: { type: mongoose.Schema.Types.ObjectId, ref: "ChatRoom", required: true },
  senderId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  content: String,
  image: String,

  aiSuggestion: [String],
  isBadManner: { type: Boolean, default: false },
  readBy: [
    {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User"
    }
  ]

}, { timestamps: true });

export default mongoose.model("ChatMessage", chatMessageSchema);
