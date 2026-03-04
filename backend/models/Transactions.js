import mongoose from "mongoose";

const transactionSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: "Post", required: true },
  buyerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  price: { type: Number, required: true },
  completedAt: { type: Date, default: Date.now }
});

export default mongoose.model("Transaction", transactionSchema);
