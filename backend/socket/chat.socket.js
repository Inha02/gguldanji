import ChatMessage from "../models/ChatMessage.js";
import ChatRoom from "../models/ChatRoom.js";
import jwt from "jsonwebtoken";

/**
 * Socket 초기화
 */
export const initSocket = (io) => {

  io.on("connection", (socket) => {

    console.log("user connected:", socket.id);

    /**
     * 채팅방 입장
     */
    socket.on("join_room", (roomId) => {

      socket.join(roomId);

      console.log(`socket ${socket.id} joined room ${roomId}`);
    });


    /**
     * 메시지 전송
     */

    socket.on("send_message", async (data) => {
  try {
    const { roomId, content, image, token } = data;

    // ⭐ 토큰에서 유저 추출
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const senderId = decoded.userId;

    const newMessage = await ChatMessage.create({
      roomId,
      senderId,
      content: content || "",
      image: image || "",
      aiSuggestion: [],
      isBadManner: false,
      readBy: [senderId]
    });

    await ChatRoom.findByIdAndUpdate(
      roomId,
      { lastMessage: content,
        updatedAt: new Date() }
    );

    const populatedMessage = await ChatMessage.findById(newMessage._id)
      .populate("senderId", "nickname profileImage");

    io.to(roomId).emit("receive_message", populatedMessage);

  } catch (error) {
    console.error("message error:", error);
  }
});

/**
    socket.on("send_message", async (data) => {

      try {

        const { roomId, senderId, content, image } = data;

        /**
         * MongoDB 저장
         
        const newMessage = await ChatMessage.create({
          roomId,
          senderId,
          content: content || "",
          image: image || "",
          aiSuggestion: [],
          isBadManner: false,

          // 보낸 사람은 읽음
          readBy: [senderId]
        });

        /**
         * 채팅방 updatedAt 업데이트
        
        await ChatRoom.findByIdAndUpdate(
          roomId,
          { updatedAt: new Date() }
        );

        /**
         * DB 저장된 메시지 조회
        
        const populatedMessage = await ChatMessage.findById(newMessage._id)
          .populate("senderId", "nickname profileImage");

        /**
         * 같은 room 사용자에게 전송
        
        io.to(roomId).emit("receive_message", populatedMessage);

      } catch (error) {

        console.error("message error:", error);

      }

    });
 */    


    /**
     * 연결 종료
     */
    socket.on("disconnect", () => {

      console.log("user disconnected:", socket.id);

    });

  });

};

/*
 프론트 채팅 메시지 예시
 {
  "roomId": "65c1b6c2e3f4a123456789ab",
  "senderId": "65c1b6c2e3f4a123456789bb",
  "content": "가격 네고 가능할까요?",
  "image": ""
}

프론트 소켓 예시
import { io } from "socket.io-client";

const socket = io("http://localhost:4000");

socket.emit("join_room", roomId);

socket.emit("send_message", {
  roomId,
  senderId,
  content: message
});

socket.on("receive_message", (data) => {
  console.log(data);
});

 */