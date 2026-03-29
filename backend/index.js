import express from "express";
import dotenv from "dotenv";
import connectDB from "./config/db.js";
import cors from "cors";
import http from "http";

import router from "./routes/user.routes.js";
import authRouter from "./routes/auth.js";
import postRoutes from "./routes/post.routes.js";
import swaggerUi from "swagger-ui-express";
import swaggerSpec from "./config/swagger.js";
import chatRoutes from "./routes/chat.routes.js";
import aiRoutes from "./routes/ai.routes.js";
import chatAiRoutes from "./routes/chat.ai.routes.js";


import  { Server } from "socket.io";
import { initSocket }  from "./socket/chat.socket.js";

import "./models/User.js";
import "./models/ChatRoom.js";
import "./models/ChatMessage.js";


dotenv.config();

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

// HTTP 서버 생성
const server = http.createServer(app);

// Socket.IO 초기화
const io = new Server(server, {
  cors: {
    origin: "*"
  }
});

initSocket(io);

// API 라우터 
app.use("/users", router);
app.use("/auth", authRouter);
app.use("/posts", postRoutes);
app.use("/chat", chatRoutes);
app.use("/ai", aiRoutes);
app.use("/chat/ai", chatAiRoutes);

// DB 연결 후 서버 시작
const startServer = async () => {
  try {
    await connectDB(); 

    server.listen(process.env.PORT, () => {
      console.log(`✅ Backend listening on port ${process.env.PORT}`);
    });

  } catch (error) {
    console.error("❌ Server start failed:", error);
    process.exit(1);
  }
};

startServer();