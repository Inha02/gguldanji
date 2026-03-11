import mongoose from "mongoose";


// 공지사항 (삭제예정)
const noticeSchema = new mongoose.Schema({
  title: String,
  content: String
}, { timestamps: true });

export default mongoose.model("Notice", noticeSchema);
