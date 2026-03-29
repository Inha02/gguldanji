import { useNavigate } from "react-router-dom";
import { useChat } from "../context/ChatContext";
import { useEffect } from "react";

export default function ChatList() {
  const navigate = useNavigate();
  const { chatRooms, setChatRooms } = useChat();
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const res = await fetch("http://localhost:4000/chat/rooms", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        // 🔥 서버 데이터 → 기존 UI 구조로 변환
        const MY_ID = JSON.parse(atob(token.split(".")[1])).userId;
        const formatted = data.rooms.map((room) => {
          const isBuyer = room.buyerId?._id === MY_ID;

          const opponent = isBuyer ? room.sellerId : room.buyerId;

          return {
            id: room._id,
            name: opponent?.nickname || "상대방",
            product: room.postId?.title || "상품",
            messages: room.lastMessage
              ? [
                  {
                    text: room.lastMessage,
                    time: "",
                  },
                ]
              : [],
          };
        });

        setChatRooms(formatted);
      } catch (err) {
        console.error("채팅방 불러오기 실패:", err);
      }
    };

    fetchRooms();
  }, []);

  return (
    <div className="chatlist-page">
      <div className="chatlist-header">
        <div className="chatlist-title text-heading-3">채팅</div>

        <button className="chatlist-kebab" type="button" aria-label="메뉴">
          <span className="chatlist-kebab-dots" />
        </button>
      </div>

      <div className="chatlist-sheet">
        <div className="chatlist-greeting text-body-2">안녕하세요, 최00님!</div>

        <div className="chatlist-divider" />

        <div className="chatlist-list">
          {chatRooms.map((chat) => {
            const lastMessage = chat.messages[chat.messages.length - 1];

            return (
              <div
                key={chat.id}
                className="chatlist-item"
                onClick={() => navigate(`/chat/${chat.id}`)}
              >
                <div className="chatlist-avatar">
                  <div className="chatlist-bear" />
                </div>

                <div className="chatlist-content">
                  <div className="chatlist-top">
                    <div className="chatlist-name text-body-1">{chat.name}</div>

                    <div className="chatlist-product text-caption">
                      {chat.product}
                    </div>
                  </div>

                  <div className="chatlist-bottom">
                    <div className="chatlist-last text-body-2">
                      {lastMessage?.text}
                    </div>

                    <div className="chatlist-time text-caption">
                      {lastMessage?.time}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
