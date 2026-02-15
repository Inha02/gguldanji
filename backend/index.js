import express from "express";
import dotenv from "dotenv";
dotenv.config();
import connectDB from "./config/db.js";
import cors from "cors";
import router from "./routes/user.routes.js";


console.log("MONGO_URI =", process.env.MONGO_URI);

// 모델 불러오기 (중요)
import "./models/User.js";

connectDB();

const app = express();
app.use(express.json());
app.use(cors());

app.listen(4000, () => {
  console.log("Server running");
});
app.listen(process.env.PORT, () => {
  console.log(`Backend listening on port ${process.env.PORT}`);
});

app.get("/", (req, res) => {
  res.send("Backend server running!");
});

app.use("/api/user", router);
// ⭐ 라우터 연결
app.use("/users", router);
