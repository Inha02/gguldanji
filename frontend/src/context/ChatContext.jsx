import { createContext, useContext, useMemo, useState } from "react";

const ChatContext = createContext(null);

const initialChatRooms = [
    {
        id: 1,
        name: "눈송이 A",
        product: "아이폰 14 pro 256GB",
        price: "650,000원",
        tag: "적정",
        messages: [
            { id: 1, side: "left", text: "안녕하세요.", time: "18:34" },
            { id: 2, side: "right", text: "안녕하세요.", time: "18:35" },
            { id: 3, side: "right", text: "궁금하신 점 편하게 물어보세요 😊", time: "18:35" },
            { id: 4, side: "left", text: "혹시 오늘 거래 가능할까요?", time: "18:35" },
            { id: 5, side: "right", text: "네, 오늘 오후 7시부터 가능해요.", time: "18:35" },
        ],
    },
    {
        id: 2,
        name: "눈송이 B",
        product: "아이폰 14 pro 256GB",
        price: "640,000원",
        tag: "저가",
        messages: [
            { id: 1, side: "left", text: "오늘 거래 가능할까요?", time: "14:20" },
            { id: 2, side: "right", text: "네, 가능합니다.", time: "14:21" },
            { id: 3, side: "left", text: "몇 시쯤 가능하신가요?", time: "14:22" },
        ],
    },
    {
        id: 3,
        name: "눈송이 C",
        product: "아이폰 14 pro 256GB",
        price: "630,000원",
        tag: "상가",
        messages: [
            { id: 1, side: "left", text: "혹시 90만원에 거래 가능할까요?", time: "11:02" },
            { id: 2, side: "right", text: "죄송하지만 어렵습니다.", time: "11:05" },
        ],
    },
    {
        id: 4,
        name: "눈송이 D",
        product: "아이폰 14 pro 256GB",
        price: "650,000원",
        tag: "적정",
        messages: [
            { id: 1, side: "left", text: "거래 감사합니다! 조심히 가세요 ~", time: "1월 13일" },
            { id: 2, side: "right", text: "감사합니다 😊", time: "1월 13일" },
        ],
    },
    {
        id: 5,
        name: "눈송이 E",
        product: "아이폰 14 pro 256GB",
        price: "655,000원",
        tag: "적정",
        messages: [
            { id: 1, side: "left", text: "궁금하신 점 편하게 물어보세요 ㅎㅎ", time: "1월 12일" },
            { id: 2, side: "right", text: "배터리 효율이 어떻게 되나요?", time: "1월 12일" },
        ],
    },
    {
        id: 6,
        name: "눈송이 F",
        product: "아이폰 14 pro 256GB",
        price: "660,000원",
        tag: "상가",
        messages: [
            { id: 1, side: "left", text: "네고는 어렵습니다.", time: "1월 10일" },
            { id: 2, side: "right", text: "네, 알겠습니다!", time: "1월 10일" },
        ],
    },
];

export function ChatProvider({ children }) {
    const [chatRooms, setChatRooms] = useState(initialChatRooms);

    const addMessageToRoom = (roomId, message) => {
        setChatRooms((prev) =>
            prev.map((room) =>
                room.id === roomId
                    ? {
                        ...room,
                        messages: [...room.messages, message],
                    }
                    : room
            )
        );
    };

    const getRoomById = (roomId) => {
        return chatRooms.find((room) => room.id === roomId);
    };

    const value = useMemo(
        () => ({
            chatRooms,
            addMessageToRoom,
            getRoomById,
        }),
        [chatRooms]
    );

    return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
}