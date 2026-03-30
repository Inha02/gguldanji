import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import bannerImage from "../icons/homebanner.svg";

export default function HomeBanner({}) {
    const navigate = useNavigate();

    const [user, setUser] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem("token");
    
        if (!token) return;
    
        const fetchUser = async () => {
            try {
                const res = await fetch("http://localhost:4000/users/me", {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
    
                const contentType = res.headers.get("content-type");

                if (!contentType || !contentType.includes("application/json")) {
                    const text = await res.text();
                    console.error("JSON이 아닌 응답:", text);
                    throw new Error("API가 JSON이 아닌 응답을 반환했습니다.");
                }

                const data = await res.json();
                console.log(data);
    
                const mappedUser = {
                    nickname: data.nickname,
                    createdAt: data.createdAt, // 백엔드 형식 맞춰야 함
                    verifiedAreas: data.verifiedAreas,
                    selling: data.selling,
                    done: data.done,
                    bought: data.bought,
                    location: data.location || "위치 미정"
                };

                console.log("mappedUser:", mappedUser);
                setUser(mappedUser);
    
            } catch (err) {
                console.error("유저 정보 불러오기 실패", err);
            }
        };
    
        fetchUser();
    }, []);

    if (!user) return null;

    return (
        <button
            className="home-banner"
            type="button"
            onClick={() => navigate("/recommend")}
        >
            <img
                src={bannerImage}
                alt=""
                className="home-banner__image"
            />

            <div className="home-banner__content">
                <div className="home-banner__text">
                    <div className="home-banner__title">{user.nickname}님의 취향,</div>
                    <div className="home-banner__sub">곰곰이가 기억했어요</div>
                </div>

                <span className="home-banner__arrow" aria-hidden="true">
                    <ChevronRight />
                </span>
            </div>
        </button>
    );
}

function ChevronRight() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
                d="M10 6l6 6-6 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}