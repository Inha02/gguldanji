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
    })

      .populate("buyerId", "nickname profileImage")
      .populate("sellerId", "nickname profileImage")
      .populate("postId", "title price images"); // ⭐ 추가

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

    // ⭐ 생성 후 다시 populate 해서 내려주기
    const populatedRoom = await ChatRoom.findById(room._id)
      .populate("buyerId", "nickname profileImage")
      .populate("sellerId", "nickname profileImage")
      .populate("postId", "title price images");

    res.status(201).json({
      message: "채팅방 생성 완료",
      room: populatedRoom
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "채팅방 생성 실패"
    });

  }
};

export const getRoomById = async (req, res) => {
  try {
    const { roomId } = req.params;
    const userId = req.user.userId; // ⭐ 이거 추가!!!

    const room = await ChatRoom.findById(roomId)
      .populate("buyerId", "nickname profileImage")
      .populate("sellerId", "nickname profileImage")
      .populate("postId", "title price images"); // ⭐ 핵심

    if (!room) {
      return res.status(404).json({ message: "채팅방 없음" });
    }

    // ⭐ 상대 계산
    const isSeller = room.sellerId._id.toString() === userId;
    const opponent = isSeller ? room.buyerId : room.sellerId;

    res.status(200).json({
      ...room.toObject(),
      opponent // ⭐ 핵심
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({ message: "채팅방 조회 실패" });
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
      .populate("postId", "title price images")
      .sort({ updatedAt: -1 });

      // ⭐ 여기 추가
    const result = rooms.map((room) => {
      const isSeller = room.sellerId._id.toString() === userId;

      const opponent = isSeller ? room.buyerId : room.sellerId;

      return {
        ...room.toObject(),
        opponent // ⭐ 핵심
      };
    });

    res.status(200).json({
      rooms: result 
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