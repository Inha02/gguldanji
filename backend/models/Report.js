import mongoose from "mongoose";


// report 필요해..? (삭제예정)
const reportSchema = new mongoose.Schema({
  reporterId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  targetUserId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  chatRoomId: { type: mongoose.Schema.Types.ObjectId, ref: "ChatRoom" },

  reason: { type: String, required: true },
  description: String
}, { timestamps: true });

export default mongoose.model("Report", reportSchema);
