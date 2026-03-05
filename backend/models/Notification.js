import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     Notification:
 *       type: object
 *       required:
 *         - userId
 *       properties:
 *         _id:
 *           type: string
 *           description: 알림 ID
 *           example: 65c1b6c2e3f4a123456789ab
 *         userId:
 *           type: string
 *           description: 알림을 받을 사용자 ID
 *           example: 65c1b6c2e3f4a123456789aa
 *         type:
 *           type: string
 *           description: 알림 종류
 *           enum:
 *             - chat
 *             - like
 *             - transaction
 *           example: chat
 *         message:
 *           type: string
 *           description: 알림 메시지
 *           example: 새로운 채팅 메시지가 도착했습니다
 *         isRead:
 *           type: boolean
 *           description: 알림 읽음 여부
 *           example: false
 *         createdAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 */


const notificationSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  type: { type: String, enum: ["chat", "like", "transaction"] },
  message: String,
  isRead: { type: Boolean, default: false }
}, { timestamps: true });

export default mongoose.model("Notification", notificationSchema);
