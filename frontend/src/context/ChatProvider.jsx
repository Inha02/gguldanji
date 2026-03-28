import { useState } from "react";
import { ChatContext } from "./ChatContext";

export function ChatProvider({ children }) {
  const [chatRooms, setChatRooms] = useState([]);

  const addMessageToRoom = (roomId, message) => {
    setChatRooms((prev) => {
      const roomExists = prev.find((room) => room.id === roomId);

      // ✅ 방이 없으면 새로 생성
      if (!roomExists) {
        return [
          ...prev,
          {
            id: roomId,
            name: "채팅방",
            messages: [message],
          },
        ];
      }

      // ✅ 기존 방에 메시지 추가
      return prev.map((room) =>
        room.id === roomId
          ? {
              ...room,
              messages: room.messages.some((m) => m.id === message.id)
                ? room.messages
                : [...room.messages, message],
            }
          : room,
      );
    });
  };

  const getRoomById = (roomId) => {
    return chatRooms.find((room) => String(room.id) === String(roomId));
  };

  const value = {
    chatRooms,
    setChatRooms,
    addMessageToRoom,
    getRoomById,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}
