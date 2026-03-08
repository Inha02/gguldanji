import express from "express";
import auth from "../middlewares/auth.js";

import {
  createOrGetRoom,
  getMyRooms,
  getMessages,
  readMessages
} from "../controllers/chat.controller.js";

const router = express.Router();

/**
 * @swagger
 * tags:
 *   name: Chat
 *   description: 채팅 관련 API
 */


/**
 * @swagger
 * /chat/rooms:
 *   post:
 *     summary: 채팅방 생성 또는 조회
 *     description: 게시글을 기준으로 구매자와 판매자의 채팅방을 생성하거나 기존 채팅방을 반환합니다.
 *     tags: [Chat]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - postId
 *               - sellerId
 *             properties:
 *               postId:
 *                 type: string
 *                 example: 65c1b6c2e3f4a123456789aa
 *               sellerId:
 *                 type: string
 *                 example: 65c1b6c2e3f4a123456789bb
 *     responses:
 *       200:
 *         description: 채팅방 반환
 */
router.post("/rooms", auth, createOrGetRoom);



/**
 * @swagger
 * /chat/rooms:
 *   get:
 *     summary: 내 채팅방 목록 조회
 *     description: 로그인한 사용자의 채팅방 목록을 조회합니다.
 *     tags: [Chat]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: 채팅방 목록 조회 성공
 */
router.get("/rooms", auth, getMyRooms);



/**
 * @swagger
 * /chat/rooms/{roomId}/messages:
 *   get:
 *     summary: 채팅 메시지 조회
 *     description: 특정 채팅방의 메시지 목록을 조회합니다.
 *     tags: [Chat]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - name: roomId
 *         in: path
 *         required: true
 *         schema:
 *           type: string
 *         example: 65c1b6c2e3f4a123456789ab
 *     responses:
 *       200:
 *         description: 메시지 목록 조회 성공
 */
router.get("/rooms/:roomId/messages", auth, getMessages);



/**
 * @swagger
 * /chat/rooms/{roomId}/read:
 *   patch:
 *     summary: 메시지 읽음 처리
 *     description: 특정 채팅방의 메시지를 읽음 상태로 변경합니다.
 *     tags: [Chat]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - name: roomId
 *         in: path
 *         required: true
 *         schema:
 *           type: string
 *         example: 65c1b6c2e3f4a123456789ab
 *     responses:
 *       200:
 *         description: 읽음 처리 성공
 */
router.patch("/rooms/:roomId/read", auth, readMessages);

export default router;