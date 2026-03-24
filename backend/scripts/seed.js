import fs from "fs";
import path from "path";
import mongoose from "mongoose";
import dotenv from "dotenv";

import User from "../models/User.js";
import Post from "../models/Post.js";
import Category from "../models/Category.js";

dotenv.config();

const __dirname = new URL('.', import.meta.url).pathname;

// JSON 파일 읽기 함수
const loadJSON = (fileName) => {
  const filePath = path.join(__dirname, "../seed", fileName);
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
};

const seedDB = async () => {
  try {
    // 1️⃣ DB 연결
    await mongoose.connect(process.env.MONGO_URI);
    console.log("✅ MongoDB 연결 완료");

    // 2️⃣ 기존 데이터 삭제 (선택)
    await User.deleteMany();
    await Post.deleteMany();
    await Category.deleteMany();

    console.log("🧹 기존 데이터 삭제 완료");

    // 3️⃣ JSON 불러오기
    const users = loadJSON("users.json");
    const posts = loadJSON("posts.json").map(post => {
      const { _id, ...rest } = post;

      return {
        ...rest,
        _id: new mongoose.Types.ObjectId()
  };
});
    const categories = loadJSON("categories.json");

    // 4️⃣ 삽입
    await User.insertMany(users);
    await Category.insertMany(categories);
    await Post.insertMany(posts);

    console.log("🎉 데이터 삽입 완료");

    process.exit();

  } catch (error) {
    console.error("❌ 에러:", error);
    process.exit(1);
  }
};

seedDB();