import express from "express";
import dotenv from "dotenv";
import connectDB from "./config/db.js";
import cors from "cors";
import router from "./routes/user.routes.js";
import authRouter from "./routes/auth.js";
import postRoutes from "./routes/post.routes.js";
import swaggerUi from "swagger-ui-express";
import swaggerSpec from "./config/swagger.js";
import "./models/User.js";

dotenv.config();

// MongoDB 연결
// console.log("MONGO_URI =", process.env.MONGO_URI);

// Middleware 설정
const app = express();
app.use(express.json());
app.use(cors());

// Swagger UI 설정
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// 기본 라우트
app.get("/", (req, res) => {
  res.send("Backend server running!");
});

// API 라우터 
app.use("/users", router);
app.use("/auth", authRouter);
app.use("/posts", postRoutes);

// DB 연결 후 서버 시작
const startServer = async () => {
  try {
    await connectDB(); 

    app.listen(process.env.PORT, () => {
      console.log(`✅ Backend listening on port ${process.env.PORT}`);
    });

  } catch (error) {
    console.error("❌ Server start failed:", error);
    process.exit(1);
  }
};

startServer();