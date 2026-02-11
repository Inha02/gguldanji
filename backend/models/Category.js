import mongoose from "mongoose";

const categorySchema = new mongoose.Schema({
  name: { type: String, required: true },
  parentId: { type: mongoose.Schema.Types.ObjectId, ref: "Category", default: null },
  depth: { type: Number, required: true }
}, { timestamps: true });

export default mongoose.model("Category", categorySchema);
