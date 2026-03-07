import mongoose from "mongoose";
import Post from "../models/Post.js";

/**
 * 게시글 생성
 */
export const createPost = async (req, res) => {
  try {
    const sellerId = req.user.id;

    const {
      title,
      description,
      images,
      categoryId,
      price,
      isFree,
      aiPriceMin,
      aiPriceMax,
      aiPriceReason,
      location
    } = req.body;

    if (!title || title.trim().length === 0) {
      return res.status(400).json({ message: "title is required" });
    }

    const post = await Post.create({
      sellerId,
      title,
      description,
      images,
      categoryId,
      price,
      isFree,
      aiPriceMin,
      aiPriceMax,
      aiPriceReason,
      location
    });

    res.status(201).json(post);

  } catch (error) {
    res.status(500).json({ message: "server error" });
  }
};




/**
 * 게시글 목록 조회
 */
export const getPosts = async (req, res) => {
  try {

    const posts = await Post.find()
      .sort({ createdAt: -1 });

    res.json(posts);

  } catch (error) {
    res.status(500).json({ message: "게시글 조회 실패" });
  }
};




/**
 * 게시글 상세 조회
 */
export const getPostById = async (req, res) => {
  try {

    const post = await Post.findById(req.params.id);

    if (!post) {
      return res.status(404).json({
        message: "게시글이 없습니다"
      });
    }

    res.json(post);

  } catch (error) {
    res.status(500).json({
      message: "게시글 조회 실패"
    });
  }
};




/**
 * 게시글 수정
 */
export const updatePost = async (req, res) => {
  try {

    const post = await Post.findById(req.params.id);

    if (!post) {
      return res.status(404).json({
        message: "게시글이 없습니다"
      });
    }

    // 작성자 검증
    if (post.sellerId.toString() !== req.user.id) {
      return res.status(403).json({
        message: "수정 권한이 없습니다"
      });
    }

    const updatedPost = await Post.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true }
    );

    res.json(updatedPost);

  } catch (error) {
    res.status(500).json({
      message: "게시글 수정 실패"
    });
  }
};




/**
 * 게시글 삭제
 */
export const deletePost = async (req, res) => {
  try {

    const post = await Post.findById(req.params.id);

    if (!post) {
      return res.status(404).json({
        message: "게시글이 없습니다"
      });
    }

    // 작성자 검증
    if (post.sellerId.toString() !== req.user.id) {
      return res.status(403).json({
        message: "삭제 권한이 없습니다"
      });
    }

    await Post.findByIdAndDelete(req.params.id);

    res.json({
      message: "게시글 삭제 완료"
    });

  } catch (error) {
    res.status(500).json({
      message: "게시글 삭제 실패"
    });
  }
};