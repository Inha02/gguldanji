import express from "express";
import dotenv from "dotenv";
import connectDB from "./config/db.js";
import cors from "cors";
import router from "./routes/user.routes.js";
import authRouter from "./routes/auth.js";
import postRoutes from "./routes/post.routes.js";
import swaggerUi from "swagger-ui-express";
import swaggerSpec from "./config/swagger.js";

dotenv.config();

console.log("MONGO_URI =", process.env.MONGO_URI);

// 모델 불러오기
import "./models/User.js";

connectDB();

const app = express();
app.use(express.json());
app.use(cors());

app.listen(process.env.PORT, () => {
  console.log(`Backend listening on port ${process.env.PORT}`);
});

app.get("/", (req, res) => {
  res.send("Backend server running!");
});

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// 라우터 연결

app.use("/api/user", router);
app.use("/users", router);
app.use("/auth", authRouter);

// post 라우터 연결 
app.use(express.json());
app.use("/posts", postRoutes);