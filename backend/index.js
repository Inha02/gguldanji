import express from "express";
import dotenv from "dotenv";
dotenv.config();
import connectDB from "./config/db.js";


console.log("MONGO_URI =", process.env.MONGO_URI);

// 모델 불러오기 (중요)
import "./models/User.js";

connectDB();

// const express = require("express");

const app = express();
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Backend server running!");
});

app.listen(process.env.PORT, () => {
  console.log(`Backend listening on port ${process.env.PORT}`);
});

// ⭐ 라우터 연결
import router from "./routes/user.routes.js";
app.use("/users", router);
