import { createContext, useContext } from "react";

// Context 생성
export const ChatContext = createContext();

// useChat 훅 (이거 없어서 에러 난 거)
export const useChat = () => {
    return useContext(ChatContext);
};