import express from "express";
import Like from "../models/Like.js";
import auth from "../middlewares/auth.js";

const router = express.Router();

/**
 * @swagger
 * tags:
 *   name: Likes
 *   description: 좋아요 API
 */

//////////////////////////////////////////////////
// ❤️ 좋아요 토글 (추가 / 취소)
//////////////////////////////////////////////////
/**
 * @swagger
 * /likes/toggle:
 *   post:
 *     summary: 좋아요 추가 또는 취소
 *     tags: [Likes]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           example:
 *             postId: "65c1b6c2e3f4a123456789bb"
 *     responses:
 *       200:
 *         description: 좋아요 상태 반환
 */
router.post("/toggle", auth, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { postId } = req.body;

    const existing = await Like.findOne({ userId, postId });

    // ❌ 이미 좋아요 있음 → 삭제
    if (existing) {
      await Like.deleteOne({ _id: existing._id });
      return res.json({ liked: false });
    }

    // ✅ 좋아요 생성
    await Like.create({ userId, postId });

    res.json({ liked: true });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "좋아요 처리 실패" });
  }
});

//////////////////////////////////////////////////
// ❤️ 특정 게시글 좋아요 수
//////////////////////////////////////////////////
/**
 * @swagger
 * /likes/count/{postId}:
 *   get:
 *     summary: 게시글 좋아요 수 조회
 *     tags: [Likes]
 */
router.get("/count/:postId", async (req, res) => {
  try {
    const { postId } = req.params;

    const count = await Like.countDocuments({ postId });

    res.json({ count });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "조회 실패" });
  }
});

//////////////////////////////////////////////////
// ❤️ 내가 좋아요 눌렀는지 확인
//////////////////////////////////////////////////
/**
 * @swagger
 * /likes/me/{postId}:
 *   get:
 *     summary: 내가 좋아요 눌렀는지 확인
 *     tags: [Likes]
 *     security:
 *       - bearerAuth: []
 */
router.get("/me/:postId", auth, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { postId } = req.params;

    const liked = await Like.exists({ userId, postId });

    res.json({ liked: !!liked });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "조회 실패" });
  }
});

export default router;