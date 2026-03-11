import mongoose from "mongoose";

//문의.. 필요한가..? (삭제예정)
const inquirySchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  title: String,
  content: String,
  status: { type: String, enum: ["pending", "answered"], default: "pending" }
}, { timestamps: true });

export default mongoose.model("Inquiry", inquirySchema);
