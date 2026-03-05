import mongoose from "mongoose";

/**
 * @swagger
 * components:
 *   schemas:
 *     Category:
 *       type: object
 *       required:
 *         - name
 *         - depth
 *       properties:
 *         _id:
 *           type: string
 *           example: 65c1b6c2e3f4a123456789ab
 *         name:
 *           type: string
 *           example: 전자기기
 *         parentId:
 *           type: string
 *           nullable: true
 *           example: 65c1b6c2e3f4a123456789aa
 *         depth:
 *           type: number
 *           example: 1
 *         createdAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           example: 2026-03-05T12:00:00Z
 */

const categorySchema = new mongoose.Schema({
  name: { type: String, required: true },
  parentId: { type: mongoose.Schema.Types.ObjectId, ref: "Category", default: null },
  depth: { type: Number, required: true }
}, { timestamps: true });

export default mongoose.model("Category", categorySchema);
