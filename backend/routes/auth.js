import express from "express";
import axios from "axios";
import jwt from "jsonwebtoken";
import User from "../models/User.js";
import dotenv from "dotenv";
import bcrypt from "bcrypt";
dotenv.config();


const router = express.Router();

router.get("/kakao", (req, res) => {
    console.log("CLIENT_ID:", process.env.KAKAO_CLIENT_ID);
    console.log("REDIRECT_URI:", process.env.KAKAO_REDIRECT_URI);

  const kakaoAuthUrl =
    `https://kauth.kakao.com/oauth/authorize?` +
    `client_id=${process.env.KAKAO_CLIENT_ID}` +
    `&redirect_uri=${process.env.KAKAO_REDIRECT_URI}` +
    `&response_type=code`;

    console.log("KAKAO URL:", kakaoAuthUrl);

  res.redirect(kakaoAuthUrl);
});

router.get("/kakao/callback", async (req, res) => {
  const { code } = req.query;

  try {
    // 1️⃣ 인가코드 → access_token 요청
    const tokenResponse = await axios.post(
      "https://kauth.kakao.com/oauth/token",
      null,
      {
        params: {
          grant_type: "authorization_code",
          client_id: process.env.KAKAO_CLIENT_ID,
          redirect_uri: process.env.KAKAO_REDIRECT_URI,
          code: code,
        },
        headers: {
          "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        },
      }
    );

    const accessToken = tokenResponse.data.access_token;

    // 2️⃣ 사용자 정보 요청
    const userResponse = await axios.get(
      "https://kapi.kakao.com/v2/user/me",
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    const kakaoUser = userResponse.data;
    const email = kakaoUser.kakao_account.email;
    const nickname = kakaoUser.properties.nickname;

    // 3️⃣ DB 조회 또는 생성
    let user = await User.findOne({ email });

    if (!user) {
      user = await User.create({
        email,
        nickname,
        socialType: "kakao",
      });
    }

    // 4️⃣ JWT 발급
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    );

    // 5️⃣ 프론트엔드로 리다이렉트 (쿼리로 JWT 전달)
    const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";
    res.redirect(`${frontendUrl}/login?token=${encodeURIComponent(token)}&userId=${user._id}`);
  } catch (error) {
    console.error(error);
    const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";
    res.redirect(`${frontendUrl}/login?error=login_failed`);
  }
});

/**
 * @swagger
 * /auth/signup:
 *   post:
 *     summary: 일반 회원가입
 *     description: 이메일과 비밀번호를 이용해 회원가입을 합니다.
 *     tags:
 *       - Auth
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
 *               gender:
 *                 type: string
 *                 enum:
 *                   - M
 *                   - F
 *                 example: F
 *               birthDate:
 *                 type: string
 *                 example: 20040101
 *     responses:
 *       201:
 *         description: 회원가입 성공
 *       400:
 *         description: 이미 가입된 이메일
 *       500:
 *         description: 서버 오류
 */
router.post("/signup", async (req, res) => {
  try {
    const { email, password, nickname, gender, birthDate } = req.body;

    // 1️⃣ 이메일 중복 체크
    const existingUser = await User.findOne({ email });

    if (existingUser) {
      return res.status(400).json({
        message: "이미 가입된 이메일입니다."
      });
    }

    // 2️⃣ 비밀번호 암호화
    const hashedPassword = await bcrypt.hash(password, 10);

    // 3️⃣ 사용자 생성
    const user = await User.create({
      email,
      password: hashedPassword,
      nickname,
      gender,
      birthDate
    });

    res.status(201).json({
      message: "회원가입 성공",
      user
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "회원가입 실패"
    });
  }
});

/**
 * @swagger
 * /auth/login:
 *   post:
 *     summary: 일반 로그인
 *     description: 이메일과 비밀번호로 로그인합니다.
 *     tags:
 *       - Auth
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
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
 *       400:
 *         description: 로그인 실패
 *       500:
 *         description: 서버 오류
 */

router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    // 1️⃣ 이메일로 사용자 찾기
    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({
        message: "사용자를 찾을 수 없습니다."
      });
    }

    // 2️⃣ 비밀번호 확인
    const isMatch = await bcrypt.compare(password, user.password);

    if (!isMatch) {
      return res.status(400).json({
        message: "비밀번호가 틀렸습니다."
      });
    }

    // 3️⃣ JWT 발급
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    );

    res.json({
      message: "로그인 성공",
      token,
      user
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "로그인 실패"
    });
  }
});

export default router;

