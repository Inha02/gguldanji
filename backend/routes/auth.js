import express from "express";
import axios from "axios";
import jwt from "jsonwebtoken";
import User from "../models/User.js";
import dotenv from "dotenv";
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

    // 5️⃣ 프론트 없이 화면 출력
    res.send(`
      <h2>카카오 로그인 성공 🎉</h2>
      <p>닉네임: ${nickname}</p>
      <p>이메일: ${email}</p>
      <p>JWT:</p>
      <textarea rows="10" cols="80">${token}</textarea>
    `);

  } catch (error) {
    console.error(error);
    res.status(500).send("로그인 실패");
  }
});

export default router;

