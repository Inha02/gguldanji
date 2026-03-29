import express from "express";
import ChatMessage from "../models/ChatMessage.js";
import ChatRoom from "../models/ChatRoom.js";
import Post from "../models/Post.js";

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     ChatLog:
 *       type: object
 *       properties:
 *         role:
 *           type: string
 *           enum: [buyer, seller]
 *           example: buyer
 *         message:
 *           type: string
 *           example: 안녕하세요 아직 판매중인가요?
 *         timestamp:
 *           type: string
 *           format: date-time
 *           example: 2026-03-01T10:00:00Z
 *
 *     AIChatFormat:
 *       type: object
 *       properties:
 *         seller_id:
 *           type: string
 *           example: 65c1b6c2e3f4a123456789ab
 *         chat_logs:
 *           type: array
 *           items:
 *             $ref: '#/components/schemas/ChatLog'
 *         existing_profile:
 *           nullable: true
 *           example: null
 *         all_chat_logs:
 *           nullable: true
 *           example: null
 */
/**
 * @swagger
 * /chat_ai/{roomId}/ai-format:
 *   get:
 *     summary: 채팅 로그를 AI 입력 형식으로 변환
 *     description: 채팅 메시지를 AI 모델 입력용 JSON 구조로 변환합니다.
 *     tags: [Chat]
 *     parameters:
 *       - in: path
 *         name: roomId
 *         required: true
 *         schema:
 *           type: string
 *         description: 채팅방 ID
 *         example: 65c1b6c2e3f4a123456789ab
 *     responses:
 *       200:
 *         description: 변환 성공
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/AIChatFormat'
 *       404:
 *         description: 채팅방 또는 게시글 없음
 *       500:
 *         description: 서버 에러
 */
router.get("/:roomId/ai-format", async (req, res) => {
  try {
    const { roomId } = req.params;

    // 1️⃣ 채팅방 조회
    const room = await ChatRoom.findById(roomId);

    if (!room) {
      return res.status(404).json({ message: "채팅방 없음" });
    }

    // 2️⃣ post 조회 → sellerId 확보
    const post = await Post.findById(room.postId);

    if (!post) {
      return res.status(404).json({ message: "게시글 없음" });
    }

    const sellerId = String(post.sellerId);

    // 3️⃣ 채팅 메시지 조회 (시간순)
    const messages = await ChatMessage.find({ roomId })
      .sort({ createdAt: 1 });

    // 4️⃣ AI 형식으로 변환
    const chatLogs = messages.map((msg) => {
      return {
        role: String(msg.senderId) === sellerId ? "seller" : "buyer",
        message: msg.content,
        timestamp: msg.createdAt
      };
    });

    // 5️⃣ 최종 JSON 구조
    const result = {
      seller_id: sellerId,
      chat_logs: chatLogs,
      existing_profile: null,
      all_chat_logs: null
    };

    res.json(result);

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "서버 에러" });
  }
});

export default router;