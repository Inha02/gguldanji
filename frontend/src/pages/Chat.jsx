import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useChat } from "../context/ChatContext";

export default function Chat() {
    const navigate = useNavigate();
    const location = useLocation();
    const { chatId } = useParams();
    const { getRoomById, addMessageToRoom } = useChat();

    const seller= location.state?.seller || {
        nickname: room?.name || "최00",
        town: "청파동"
    };

    const productTitle = location.state?.product || "상품명";
    const productPrice = location.state?.price || "가격";

    const roomId = Number(chatId);
    const room = getRoomById(roomId);

    const [inputValue, setInputValue] = useState("");

    if (!room) {
        return <div className="chat-page">채팅방을 찾을 수 없습니다.</div>;
    }

    const getCurrentTime = () => {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, "0");
        const minutes = String(now.getMinutes()).padStart(2, "0");
        return `${hours}:${minutes}`;
    };

    const handleSendMessage = () => {
        const trimmed = inputValue.trim();
        if (!trimmed) return;

        const newMessage = {
            id: Date.now(),
            side: "right",
            text: trimmed,
            time: getCurrentTime(),
        };

        addMessageToRoom(roomId, newMessage);
        setInputValue("");
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const tagClassName =
        room.tag === "저가"
            ? "chat-topcard__tag--low"
            : room.tag === "상가"
                ? "chat-topcard__tag--high"
                : "chat-topcard__tag--fair";

    return (
        <div className="chat-page">
            {/* Header */}
            <div className="chat-header">
                <div className="chat-header__left">
                    <button
                        className="chat-header__back"
                        aria-label="뒤로가기"
                        onClick={() => navigate("/chat")}
                        type="button"
                    >
                        <span className="chat-back-icon" />
                    </button>

                    <div className="chat-header__name">{seller.nickname}</div>
                </div>

                <button
                    className="chat-header__kebab"
                    aria-label="메뉴"
                    type="button"
                >
                    <span className="chat-kebab-dots" />
                </button>
            </div>

            {/* 상품 정보 */}
            <div className="chat-topcard">
                <div className="chat-topcard__row">
                    <div className="chat-topcard__thumb" />

                    <div className="chat-topcard__info">
                        <div className="chat-topcard__product">
                            {productTitle}
                        </div>
                        <div className="chat-topcard__price">
                            {productPrice}
                        </div>
                    </div>

                    <div className={`chat-topcard__tag ${tagClassName}`}>
                        {room.tag}
                    </div>
                </div>
            </div>

            {/* 흰 박스 */}
            <div className="chat-sheet">
                <div className="chat-body">
                    <div className="chat-date-pill">1월 14일</div>

                    {room.messages.map((m) => (
                        <div
                            key={m.id}
                            className={`chat-row ${m.side === "right" ? "is-right" : "is-left"}`}
                        >
                            {m.side === "left" && (
                                <div className="chat-avatar" aria-hidden="true" />
                            )}

                            <div className="chat-bubble-wrap">
                                <div
                                    className={`chat-bubble ${m.side === "right"
                                            ? "bubble-right"
                                            : "bubble-left"
                                        }`}
                                >
                                    {m.text}
                                </div>

                                <div
                                    className={`chat-time ${m.side === "right"
                                            ? "time-right"
                                            : "time-left"
                                        }`}
                                >
                                    {m.time}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="chat-inputbar">
                    <button
                        className="chat-plus"
                        type="button"
                        aria-label="추가"
                    >
                        +
                    </button>

                    <input
                        className="chat-inputfake"
                        type="text"
                        placeholder="메시지 보내기"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />

                    <button
                        className="chat-send"
                        type="button"
                        aria-label="전송"
                        onClick={handleSendMessage}
                    >
                        <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                        >
                            <path
                                d="M3 11.5L21 3l-8.5 18-2.5-7-7-2.5z"
                                fill="none"
                                stroke="#FDFDFD"
                                strokeWidth="2"
                                strokeLinejoin="round"
                            />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
