import express from "express";
import User from "../models/User.js";

const router = express.Router();

// 회원가입
router.post("/", async (req, res) => {
  try {
    const user = await User.create(req.body);
    res.status(201).json(user);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});

export default router;
