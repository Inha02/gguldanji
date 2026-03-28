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
import ProfileView from "./pages/ProfileView";
import NeighborhoodManage from "./pages/NeighborhoodManage";
import NeighborhoodAdd from "./pages/NeighborhoodAdd";
import SignUp from "./pages/SignUp";
import Notifications from "./pages/Notifications";
import ProductDetail from "./pages/ProductDetail";
import Onboarding from "./pages/Onboarding";
import Search from "./pages/Search";
import SearchResult from "./pages/SearchResult";

export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Home />} />
            <Route path="/likes" element={<Likes />} />
            <Route path="/post" element={<Post />} />
            <Route path="/chat" element={<ChatList />} />
            <Route path="/mypage" element={<MyPage />} />
            <Route path="/recommend" element={<Recommend />} />
            <Route path="/category" element={<Category />} />
            <Route path="/login" element={<Login />} />
            <Route path="/profile-view" element={<ProfileView />} />
            <Route path="/NeighborhoodManage" element={<NeighborhoodManage />} />
            <Route path="/NeighborhoodAdd" element={<NeighborhoodAdd />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/search" element={<Search />} /> 
            <Route path="/search-result" element={<SearchResult />} />
          </Route>

          <Route element={<ChatShell />}>
            <Route path="/chat/:chatId" element={<Chat />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ChatProvider>
  );
}