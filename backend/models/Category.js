import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     CategoryInfo:
 *       type: object
 *       required:
 *         - name
 *       properties:
 *         _id:
 *           type: string
 *           example: 65c1b6c2e3f4a123456789ab
 *         name:
 *           type: string
 *           example: 전자기기
 *         recommended_attributes:
 *           type: array
 *           items:
 *             type: string
 *           example: ["브랜드", "모델명", "용량"]
 *         optional_attributes:
 *           type: array
 *           items:
 *             type: string
 *           example: ["구성품", "구매시기"]
 *         createdAt:
 *           type: string
 *           format: date-time
 *         updatedAt:
 *           type: string
 *           format: date-time
 */

const categorySchema = new mongoose.Schema(
  {
    name: { type: String, required: true },

    // 필수 추천 속성
    recommended_attributes: {
      type: [String],
      default: []
    },

    // 선택 속성
    optional_attributes: {
      type: [String],
      default: []
    }
  },
  { timestamps: true }
);

export default mongoose.model("Category", categorySchema);
