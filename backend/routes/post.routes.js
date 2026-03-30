import express from "express";
import auth from "../middlewares/auth.js";
import multer from "multer";
import path from "path";

import {
  createPost,
  getPosts,
  getPostById,
  updatePost,
  deletePost
} from "../controllers/post.controller.js";
const router = express.Router();
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname); // ⭐ 확장자 추출 (.jpg)
    cb(null, Date.now() + ext); // ⭐ 파일명 + 확장자
  }
});

const upload = multer({ storage });

/**
 * @swagger
 * tags:
 *   name: Posts
 *   description: 중고거래 게시글 API
 */


/**
 * @swagger
 * /posts:
 *   post:
 *     summary: 게시글 생성
 *     description: 로그인한 사용자가 게시글을 생성합니다.
 *     tags: [Posts]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - title
 *               - price
 *             properties:
 *               title:
 *                 type: string
 *                 example: 아이폰 13 팝니다
 *               price:
 *                 type: number
 *                 example: 500000
 *               description:
 *                 type: string
 *                 example: 사용감 조금 있습니다
 *               category:
 *                 type: string
 *                 example: electronics
 *               location:
 *                 type: string
 *                 example: 서울 용산구
 *     responses:
 *       201:
 *         description: 게시글 생성 성공
 *       401:
 *         description: 인증 실패
 */
router.post("/", auth, upload.array("images"), createPost);


/**
 * @swagger
 * /posts:
 *   get:
 *     summary: 게시글 목록 조회
 *     description: 전체 게시글을 조회합니다.
 *     tags: [Posts]
 *     responses:
 *       200:
 *         description: 게시글 목록 조회 성공
 */
router.get("/", getPosts);


/**
 * @swagger
 * /posts/{id}:
 *   get:
 *     summary: 게시글 상세 조회
 *     description: 특정 게시글을 조회합니다.
 *     tags: [Posts]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         example: 65b2e3f4a1b2c3d4e5f6
 *     responses:
 *       200:
 *         description: 게시글 조회 성공
 *       404:
 *         description: 게시글 없음
 */
router.get("/:id", getPostById);

/**
 * @swagger
 * /posts/{id}:
 *   patch:
 *     summary: 게시글 수정
 *     description: 게시글을 수정합니다.
 *     tags: [Posts]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         example: 65b2e3f4a1b2c3d4e5f6
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               title:
 *                 type: string
 *                 example: 아이폰 13 가격 인하
 *               price:
 *                 type: number
 *                 example: 450000
 *     responses:
 *       200:
 *         description: 게시글 수정 성공
 *       401:
 *         description: 인증 실패
 */
router.patch("/:id", auth, updatePost);


/**
 * @swagger
 * /posts/{id}:
 *   delete:
 *     summary: 게시글 삭제
 *     description: 게시글을 삭제합니다.
 *     tags: [Posts]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         example: 65b2e3f4a1b2c3d4e5f6
 *     responses:
 *       200:
 *         description: 게시글 삭제 성공
 *       401:
 *         description: 인증 실패
 */
router.delete("/:id", auth, deletePost);

export default router;