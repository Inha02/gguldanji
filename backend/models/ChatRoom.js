import mongoose from "mongoose";

const chatRoomSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: "Post", required: true },
  buyerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  lastMessage: String
}, { timestamps: true });

export default mongoose.model("ChatRoom", chatRoomSchema);
