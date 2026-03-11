import { BrowserRouter, Routes, Route } from "react-router-dom";

import AppShell from "./components/AppShell";
import ChatShell from "./components/ChatShell";

import Home from "./pages/Home";
import Likes from "./pages/Likes";
import ChatList from "./pages/ChatList";
import Chat from "./pages/Chat";
import Post from "./pages/Post";
import MyPage from "./pages/MyPage";
import Recommend from "./pages/Recommend";
import Category from "./pages/Category";
import Login from "./pages/Login";
import { ChatProvider } from "./context/ChatContext";


export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <Routes>
          {/* 전부 AppShell 안: device 프레임 유지 */}
          <Route element={<AppShell />}>
            <Route path="/" element={<Home />} />
            <Route path="/likes" element={<Likes />} />
            <Route path="/post" element={<Post />} />
            <Route path="/chat" element={<ChatList />} />
            <Route path="/mypage" element={<MyPage />} />
            <Route path="/recommend" element={<Recommend />} />

            {/* 프레임 유지 + AppShell에서 네비 숨김 처리 */}
            <Route path="/category" element={<Category />} />
            <Route path="/login" element={<Login />} />
          </Route>

        {/* 채팅 상세는 네비 없어야 하니까 ChatShell 그대로 유지 */}
          <Route element={<ChatShell />}>
            <Route path="/chat/:chatId" element={<Chat />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ChatProvider>
  );
}