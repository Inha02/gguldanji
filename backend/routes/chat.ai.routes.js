import express from "express";
import ChatMessage from "../models/ChatMessage.js";
import ChatRoom from "../models/ChatRoom.js";
import Post from "../models/Post.js";

const router = express.Router();

/**
 * @swagger
 * /chat/{roomId}/ai-format:
 *   get:
 *     summary: 채팅 로그를 AI 입력 형식으로 변환
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