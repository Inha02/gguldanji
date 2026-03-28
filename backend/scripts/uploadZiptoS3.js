import fs from "fs";
import AWS from "aws-sdk";
import unzipper from "unzipper";
import dotenv from "dotenv";

dotenv.config();

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

const BUCKET = process.env.S3_BUCKET;

// ⭐ 추가: 파일 존재 확인
async function fileExists(key) {
  try {
    await s3.headObject({
      Bucket: BUCKET,
      Key: key
    }).promise();
    return true;
  } catch (err) {
    if (err.code === "NotFound") return false;
    throw err;
  }
}

async function uploadZipToS3() {
  const stream = fs.createReadStream("images.zip")
    .pipe(unzipper.Parse({ forceStream: true }));

  for await (const entry of stream) {
    const filePath = entry.path;
    const type = entry.type;

    if (type === "File") {
      const contentType =
        filePath.endsWith(".png") ? "image/png" : "image/jpeg";

      try {
        // ⭐ 이미 있는지 확인
        const exists = await fileExists(filePath);

        if (exists) {
          console.log("⏭️ 이미 있음:", filePath);
          entry.autodrain(); // 중요!
          continue;
        }

        // ⭐ 업로드
        await s3.upload({
          Bucket: BUCKET,
          Key: filePath,
          Body: entry,
          ContentType: contentType
        }).promise();

        console.log("✅ 업로드:", filePath);

      } catch (err) {
        console.error("❌ 실패:", filePath, err.message);
        entry.autodrain(); // 실패해도 스트림 비워줘야 함
      }

    } else {
      entry.autodrain();
    }
  }

  console.log("🚀 전체 업로드 완료");
}

uploadZipToS3();