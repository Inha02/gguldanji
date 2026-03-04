import express from "express";
import User from "../models/User.js";
import jwt from "jsonwebtoken";
import auth from "../middlewares/auth.js";

const router = express.Router();

/**
 * @swagger
 * tags:
 *   name: Users
 *   description: 사용자 API
 */


/**
 * @swagger
 * /users:
 *   post:
 *     summary: 회원가입
 *     description: 새로운 사용자를 생성합니다.
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *               - nickname
 *             properties:
 *               email:
 *                 type: string
 *                 example: inha@test.com
 *               password:
 *                 type: string
 *                 example: 1234
 *               nickname:
 *                 type: string
 *                 example: 곰곰이
 *     responses:
 *       201:
 *         description: 회원가입 성공
 *       400:
 *         description: 회원가입 실패
 */
router.post("/", async (req, res) => {
  try {
    const user = await User.create(req.body);
    res.status(201).json(user);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});


/**
 * @swagger
 * /users/login:
 *   post:
 *     summary: 로그인
 *     description: 이메일과 비밀번호로 로그인 후 JWT 토큰을 반환합니다.
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *                 example: inha@test.com
 *               password:
 *                 type: string
 *                 example: 1234
 *     responses:
 *       200:
 *         description: 로그인 성공
 *       401:
 *         description: 로그인 실패
 */
router.post("/login", async (req, res) => {
  try {

    const { email, password } = req.body;

    const user = await User.findOne({ email });

    if (!user || user.password !== password) {
      return res.status(401).json({ message: "로그인 실패" });
    }

    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET || "secretkey",
      { expiresIn: "1d" }
    );

    res.json({ token });

  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});


/**
 * @swagger
 * /users/me:
 *   get:
 *     summary: 내 정보 조회
 *     description: 로그인한 사용자의 정보를 조회합니다.
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: 사용자 정보 조회 성공
 *       401:
 *         description: 인증 실패
 */
router.get("/me", auth, async (req, res) => {

  const user = await User.findById(req.user.userId).select("-password");

  res.json(user);

});


/**
 * @swagger
 * /users/me:
 *   patch:
 *     summary: 내 정보 수정
 *     description: 사용자 정보를 수정합니다.
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               nickname:
 *                 type: string
 *                 example: 새로운닉네임
 *     responses:
 *       200:
 *         description: 사용자 정보 수정 성공
 */
router.patch("/me", auth, async (req, res) => {

  const user = await User.findByIdAndUpdate(
    req.user.userId,
    req.body,
    { new: true }
  );

  res.json(user);

});




export default router;