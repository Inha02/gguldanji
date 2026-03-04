import mongoose from "mongoose";

const postSchema = new mongoose.Schema({
  sellerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },

  title: { type: String, required: true },
  description: String,
  images: [String],

  categoryId: { type: mongoose.Schema.Types.ObjectId, ref: "Category" },

  price: Number,
  isFree: { type: Boolean, default: false },

  aiPriceMin: Number,
  aiPriceMax: Number,
  aiPriceReason: String,

  location: {
    address: String,
    lat: Number,
    lng: Number
  },

  status: {
    type: String,
    enum: ["selling", "reserved", "sold"],
    default: "selling"
  },

  viewCount: { type: Number, default: 0 },
  likeCount: { type: Number, default: 0 }

}, { timestamps: true });

export default mongoose.model("Post", postSchema);
