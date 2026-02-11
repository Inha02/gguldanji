import mongoose from "mongoose";

const userSchema = new mongoose.Schema({
  email: { type: String, unique: true, sparse: true },
  password: { type: String },

  socialType: { type: String, enum: ["kakao", "naver", null], default: null },
  socialId: { type: String },

  nickname: { type: String, required: true },
  gender: { type: String, enum: ["M", "F"] },
  birthDate: { type: String }, // YYYYMMDD

  profileImage: String,

  trustScore: { type: Number, default: 0 },
  sellerType: { type: String }, // 친절형 / 무응답형 / 공격형

  likedCategories: [{ type: mongoose.Schema.Types.ObjectId, ref: "Category" }],
  blockedUsers: [{ type: mongoose.Schema.Types.ObjectId, ref: "User" }],

  status: {
    type: String,
    enum: ["active", "suspended", "deleted"],
    default: "active"
  }
}, { timestamps: true });

export default mongoose.model("User", userSchema);
