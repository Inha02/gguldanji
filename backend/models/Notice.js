import mongoose from "mongoose";

const noticeSchema = new mongoose.Schema({
  title: String,
  content: String
}, { timestamps: true });

export default mongoose.model("Notice", noticeSchema);
