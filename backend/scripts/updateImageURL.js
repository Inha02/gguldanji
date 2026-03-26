import mongoose from "mongoose";
import dotenv from "dotenv";
import Post from "../models/Post.js";

dotenv.config();

async function run() {
  try {
    // 1️⃣ DB 연결
    await mongoose.connect(process.env.MONGO_URI);
    console.log("✅ MongoDB 연결 완료");

    // 2️⃣ 업데이트 실행
    const result = await Post.updateMany(
      {},
      [
        {
          $set: {
            images: {
              $map: {
                input: "$images",
                as: "img",
                in: {
                  $concat: [
                    // ⭐ S3 prefix (네 환경 맞춤)
                    "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/posts/",
                    
                    // ⭐ 기존 경로 그대로 붙이기
                    "$$img"
                  ]
                }
              }
            }
          }
        }
      ],
      { updatePipeline: true } // ⭐ 이거 추가
    );

    console.log("🚀 업데이트 완료:", result.modifiedCount, "개 문서 수정됨");

  } catch (err) {
    console.error("❌ 에러:", err);
  } finally {
    // 3️⃣ 종료
    await mongoose.disconnect();
    process.exit();
  }
}

run();