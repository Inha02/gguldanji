import { useState, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { useChat } from "../context/ChatContext";
import { useEffect } from "react";
import { getSocket } from "../socket/socket";

export default function Chat() {
  const navigate = useNavigate();
  const location = useLocation();
  const { chatId } = useParams();
  const { getRoomById, addMessageToRoom, addRoom } = useChat();
  const socket = getSocket();

  const roomId = chatId;
  const room = getRoomById(roomId);
  const isSendingRef = useRef(false);
  const sendingRef = useRef(false);

  const seller = location.state?.seller || {
    nickname: room?.name || "최00",
    town: "청파동",
  };

  // 여기
  // const productTitle = location.state?.product ||  "상품명";
  // const productPrice = location.state?.price ||  "가격";

  const productTitle = location.state?.product || room?.product || "상품명";
  const productPrice = location.state?.price || room?.price || "가격";

  // const productTitle = location.state?.product || room?.post?.title || "상품명";
  // const productPrice = location.state?.price || room?.post?.price || "가격";

  const [inputValue, setInputValue] = useState("");
  const token = localStorage.getItem("token");
  function getUserIdFromToken(token) {
    if (!token) return null;

    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.userId;
  }
  const MY_ID = getUserIdFromToken(token);
  useEffect(() => {
    const init = async () => {
      try {
        // 1️⃣ 방 먼저 가져오기
        const resRoom = await fetch(
          `http://localhost:4000/chat/rooms/${roomId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        const roomData = await resRoom.json();

        addRoom({
          id: roomData._id,
          name: roomData.opponent?.nickname,
          post: roomData.postId,
          product: roomData.postId?.title,
          price: roomData.postId?.price,

          messages: [],
          tag: "적정",
        });

        // 2️⃣ 메시지 가져오기
        const resMsg = await fetch(
          `http://localhost:4000/chat/rooms/${roomId}/messages`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        const data = await resMsg.json();

        data.messages.forEach((msg) => {
          addMessageToRoom(roomId, {
            id: msg._id,
            side: msg.senderId._id === MY_ID ? "right" : "left",
            text: msg.content,
            time: new Date(msg.createdAt).toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
              hour12: true,
            }),
            profileImage: msg.senderId?.profileImage,
          });
        });

        // 3️⃣ 읽음 처리
        await fetch(`http://localhost:4000/chat/rooms/${roomId}/read`, {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      } catch (err) {
        console.error("❌ init 에러:", err);
      }
    };

    init();
  }, [roomId]);
  /*
  useEffect(() => {
    const fetchMessages = async () => {
      const res = await fetch(
        `http://localhost:4000/chat/rooms/${roomId}/messages`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const data = await res.json();

      data.messages.forEach((msg) => {
        const exists = room?.messages?.some((m) => m.id === msg._id);
        if (exists) return;
        const newMessage = {
          id: msg._id,
          side: msg.senderId._id === MY_ID ? "right" : "left",
          text: msg.content,
          time: new Date(msg.createdAt).toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
          }),
        };

        addMessageToRoom(roomId, newMessage);
      });
    };

    fetchMessages();

    fetch(`http://localhost:4000/chat/rooms/${roomId}/read`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }, [roomId]);

  useEffect(() => {
    const fetchRoom = async () => {
      if (room) return;

      try {
        const res = await fetch(`http://localhost:4000/chat/rooms/${roomId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const data = await res.json();
        console.log("room fetch:", data);
        console.log("🔥 addRoom 데이터:", data);
        console.log("🔥 최종 room:", room);

        addRoom({
          id: data._id,
          // name: data.sellerId?.nickname || "판매자",
          name: data.opponent?.nickname || "사용자", // ⭐ 핵심
          post: data.postId, // ⭐ 핵심
          product: data.postId?.title, // ⭐ 추가
          price: data.postId?.price, // ⭐ 추가
          messages: [],
          tag: "적정",
        });
      } catch (err) {
        console.error("room 불러오기 실패:", err);
      }
    };

    fetchRoom();
  }, [roomId]);
  */

  const joinedRef = useRef(false);

  useEffect(() => {
    if (!roomId || joinedRef.current) return;

    // 채팅방 입장
    socket.emit("join_room", roomId);
    joinedRef.current = true;

    // 실시간 메시지
    socket.on("receive_message", (msg) => {
      const exists = room?.messages?.find((m) => m.id === msg._id);
      if (exists) return;

      setTimeout(() => {
        addMessageToRoom(roomId, {
          id: msg._id,
          side: msg.senderId?._id === MY_ID ? "right" : "left",
          text: msg.content,
          time: new Date(msg.createdAt).toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
          }),
        });
      }, 0);
    });

    return () => {
      socket.off("receive_message");
    };
  }, [roomId]);

  if (!room) {
    // return <div className="chat-page">채팅방을 찾을 수 없습니다.</div>;
    return <div className="chat-page">로딩중...</div>;
  }

  /* 시간 
    const getCurrentTime = () => {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, "0");
        const minutes = String(now.getMinutes()).padStart(2, "0");
        return `${hours}:${minutes}`;
    };
    */
  const handleSendMessage = () => {
    if (sendingRef.current) return; // ⭐ 추가
    sendingRef.current = true;

    const trimmed = inputValue.trim();
    if (!trimmed) {
      sendingRef.current = false;
      return;
    }

    // ⭐ 1. UI 먼저 반영 (핵심)
    const tempMessage = {
      id: Date.now(), // 임시 id
      side: "right",
      text: trimmed,
      time: new Date().toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }),
    };

    addMessageToRoom(roomId, tempMessage);

    // ⭐ 2. 서버 전송
    socket.emit("send_message", {
      roomId,
      content: trimmed,
      image: "",
      token: token,
    });

    // ⭐ 3. 입력창 초기화
    setInputValue("");

    setTimeout(() => {
      sendingRef.current = false;
    }, 100);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      if (isSendingRef.current) return; // ⭐ 중복 방지
      isSendingRef.current = true;

      handleSendMessage();

      setTimeout(() => {
        isSendingRef.current = false;
      }, 100);
    }
  };

  const today = new Date();

  const formattedDate = `${today.getMonth() + 1}월 ${today.getDate()}일`;

  function getImageUrl(path) {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return `http://localhost:4000/${path}`;
  }

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

        <button className="chat-header__kebab" aria-label="메뉴" type="button">
          <span className="chat-kebab-dots" />
        </button>
      </div>

      {/* 상품 정보 */}
      <div className="chat-topcard">
        <div className="chat-topcard__row">
          {room?.post?.images?.[0] ? (
            <img
              src={getImageUrl(room.post.images[0])}
              alt="상품 이미지"
              className="chat-topcard__thumb"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          ) : (
            <div className="chat-topcard__thumb" />
          )}

          <div className="chat-topcard__info">
            <div className="chat-topcard__product">{productTitle}</div>
            <div className="chat-topcard__price">{productPrice}</div>
          </div>
        </div>
      </div>

      {/* 흰 박스 */}
      <div className="chat-sheet">
        <div className="chat-body">
          <div className="chat-date-pill">{formattedDate}</div>

          {room.messages.map((m) => (
            <div
              // key={m.id}
              key={`${m.id}-${m.time}`}
              className={`chat-row ${m.side === "right" ? "is-right" : "is-left"}`}
            >
              {m.side === "left" &&
                (m.profileImage ? (
                  <img
                    src={m.profileImage}
                    alt="프로필"
                    className="chat-avatar"
                    onError={(e) => {
                      e.currentTarget.src =
                        "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/image+6.png";
                    }}
                  />
                ) : (
                  <img
                    src="https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/image+6.png"
                    alt="기본 프로필"
                    className="chat-avatar"
                  />
                ))}

              <div className="chat-bubble-wrap">
                <div
                  className={`chat-bubble ${
                    m.side === "right" ? "bubble-right" : "bubble-left"
                  }`}
                >
                  {m.text}
                </div>

                <div
                  className={`chat-time ${
                    m.side === "right" ? "time-right" : "time-left"
                  }`}
                >
                  {m.time}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="chat-inputbar">
          <button className="chat-plus" type="button" aria-label="추가">
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
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
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
