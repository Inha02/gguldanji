import mongoose from "mongoose";

const chatMessageSchema = new mongoose.Schema({
  roomId: { type: mongoose.Schema.Types.ObjectId, ref: "ChatRoom", required: true },
  senderId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  content: String,
  image: String,

  aiSuggestion: [String],
  isBadManner: { type: Boolean, default: false }

}, { timestamps: true });

export default mongoose.model("ChatMessage", chatMessageSchema);
