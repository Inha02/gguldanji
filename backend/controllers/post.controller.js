import mongoose from "mongoose";
import Post from "../models/Post.js";

const createPost = async (req, res) => {
  try {
    const sellerId = req.user.id;

    const {
      title,
      description,
      images,        // JSON 등록 시 ["url1","url2"] 형태로 받는 걸 가정
      categoryId,
      price,
      isFree,
      aiPriceMin,
      aiPriceMax,
      aiPriceReason,
      location
    } = req.body;

    // 1) 필수값 체크
    if (!title || title.trim().length === 0) {
      return res.status(400).json({ message: "title is required" });
    }

    // 2) ObjectId 형태 체크(선택값이어도 들어오면 검증)
    if (categoryId && !mongoose.isValidObjectId(categoryId)) {
      return res.status(400).json({ message: "invalid categoryId" });
    }

    // 3) 가격 규칙
    let finalIsFree = Boolean(isFree);
    let finalPrice = price;

    if (finalIsFree) {
      finalPrice = 0;
    } else {
      if (finalPrice === undefined || finalPrice === null) finalPrice = 0;
      if (Number(finalPrice) < 0) {
        return res.status(400).json({ message: "price must be >= 0" });
      }
    }

    // 4) location 형태(선택)
    // location: { address, lat, lng }
    // lat/lng 숫자 여부 정도만 체크 (강하게 하려면 범위검사도 가능)
    if (location?.lat !== undefined && typeof location.lat !== "number") {
      return res.status(400).json({ message: "location.lat must be number" });
    }
    if (location?.lng !== undefined && typeof location.lng !== "number") {
      return res.status(400).json({ message: "location.lng must be number" });
    }

    // 5) DB 저장
    const post = await Post.create({
      sellerId,
      title: title.trim(),
      description,
      images: Array.isArray(images) ? images : [],
      categoryId: categoryId || undefined,

      price: finalPrice,
      isFree: finalIsFree,

      aiPriceMin,
      aiPriceMax,
      aiPriceReason,

      location
    });

    return res.status(201).json(post);
  } catch (e) {
    console.error(e);
    return res.status(500).json({ message: "server error" });
  }
};
export default createPost;
