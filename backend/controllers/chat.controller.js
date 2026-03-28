import ChatRoom from "../models/ChatRoom.js";
import ChatMessage from "../models/ChatMessage.js";



/**
 * 1️⃣ 채팅방 생성 또는 기존 채팅방 조회
 */
export const createOrGetRoom = async (req, res) => {
  try {

    const { postId, sellerId } = req.body;

    const buyerId = req.user.userId;

    let room = await ChatRoom.findOne({
      postId,
      buyerId,
      sellerId
    });

    if (room) {
      return res.status(200).json({
        message: "기존 채팅방 반환",
        room
      });
    }

    room = await ChatRoom.create({
      postId,
      buyerId,
      sellerId,
      lastMessage: ""
    });

    res.status(201).json({
      message: "채팅방 생성 완료",
      room
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "채팅방 생성 실패"
    });

  }
};





/**
 * 2️⃣ 내 채팅방 목록 조회
 */
export const getMyRooms = async (req, res) => {

  try {

    const userId = req.user.userId;

    const rooms = await ChatRoom.find({
      $or: [
        { buyerId: userId },
        { sellerId: userId }
      ]
    })
      .populate("buyerId", "nickname profileImage")
      .populate("sellerId", "nickname profileImage")
      .populate("postId", "title")
      .sort({ updatedAt: -1 });

    res.status(200).json({
      rooms
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "채팅방 조회 실패"
    });

  }

};





/**
 * 3️⃣ 채팅 메시지 조회
 */
export const getMessages = async (req, res) => {

  try {

    const { roomId } = req.params;

    const page = Number(req.query.page) || 1;

    const limit = Number(req.query.limit) || 20;

    const skip = (page - 1) * limit;

    const messages = await ChatMessage.find({ roomId })
      .populate("senderId", "nickname profileImage")
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);

    res.status(200).json({
      messages: messages.reverse()
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "메시지 조회 실패"
    });

  }

};






/**
 * 4️⃣ 읽음 처리
 * (현재 스키마에 read 필드가 없기 때문에
 * 메시지 조회 성공 응답만 반환)
 */
export const readMessages = async (req, res) => {

  try {

    const { roomId } = req.params;

    const messages = await ChatMessage.find({ roomId });

    res.status(200).json({
      message: "읽음 처리 완료",
      messages
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "읽음 처리 실패"
    });

  }

};