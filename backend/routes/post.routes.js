import express from "express";
import  auth  from "../middlewares/auth.js";
import createPost from "../controllers/post.controller.js";

const router = express.Router();

// 🔐 로그인한 사람만 가능
router.post("/", auth, createPost);
router.get("/", (req, res) => {
  res.send("게시글 목록 조회");
});

export default router;