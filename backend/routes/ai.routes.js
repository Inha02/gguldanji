import express from "express";

import {
  aiHealth,
  estimatePrice
} from "../controllers/ai.controller.js";

const router = express.Router();

/**
 * @swagger
 * tags:
 *   name: AI
 *   description: AI 엔진(FastAPI) 연동 API
 */

/**
 * @swagger
 * /ai/health:
 *   get:
 *     summary: AI 엔진 상태 확인
 *     description: FastAPI 기반 ai-engine의 상태를 확인합니다.
 *     tags: [AI]
 *     responses:
 *       200:
 *         description: ai-engine 정상 응답
 *       502:
 *         description: ai-engine 연결 실패
 */
router.get("/health", aiHealth);

/**
 * @swagger
 * /ai/price-estimate:
 *   post:
 *     summary: AI 가격 산정
 *     description: 게시글 정보를 기반으로 ai-engine이 적정 가격 범위를 산정합니다.
 *     tags: [AI]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               title:
 *                 type: string
 *                 description: 상품 제목
 *                 example: 아이폰 13 128GB 미개봉
 *               description:
 *                 type: string
 *                 description: 상품 상세 설명
 *                 example: 개봉만 하고 사용 안 했습니다.
 *               categoryId:
 *                 type: string
 *                 description: 카테고리 ID
 *                 example: 65c1b6c2e3f4a123456789aa
 *               price:
 *                 type: number
 *                 description: 사용자가 입력한 희망 가격
 *                 example: 650000
 *               images:
 *                 type: array
 *                 items:
 *                   type: string
 *                 description: 이미지 URL 목록
 *     responses:
 *       200:
 *         description: ai-engine 가격 추천 결과
 *       400:
 *         description: 잘못된 입력 값
 *       502:
 *         description: ai-engine 연결 실패
 */
router.post("/price-estimate", estimatePrice);

export default router;

