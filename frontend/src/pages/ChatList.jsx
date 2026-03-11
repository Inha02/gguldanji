import { useNavigate } from "react-router-dom";
import { useChat } from "../context/ChatContext";

export default function ChatList() {
    const navigate = useNavigate();
    const { chatRooms } = useChat();

    return (
        <div className="chatlist-page">
            <div className="chatlist-header">
                <div className="chatlist-title text-heading-3">채팅</div>

                <button className="chatlist-kebab" type="button" aria-label="메뉴">
                    <span className="chatlist-kebab-dots" />
                </button>
            </div>

            <div className="chatlist-sheet">
                <div className="chatlist-greeting text-body-2">
                    안녕하세요, 최00님!
                </div>

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
                                        <div className="chatlist-name text-body-1">
                                            {chat.name}
                                        </div>

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