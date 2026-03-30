import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import ProfileAvatar from "../components/ProfileAvatar";

import packageIcon from "../icons/mynaui_package.svg";
import locationIcon from "../icons/mynaui_location-edit.svg";
import wrenchIcon from "../icons/mynaui_blackwrench.svg";
import userIcon from "../icons/mynaui_user.svg";

export default function MyPage() {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);

    const handleLogout = () => {
        localStorage.removeItem("token");
        navigate("/login");
    };

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
                    createdAt: data.createdAt,
                    verifiedAreas: data.verifiedAreas,
                    selling: data.selling,
                    done: data.done,
                    bought: data.bought,
                    location: data.location || "위치 미정",
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
        <div className="mypage-page">
            <div className="mypage-header">
                <div className="mypage-title">마이페이지</div>
            </div>

            <div className="mypage-main">
                <div className="mypage-profile">
                    <div className="mypage-avatar">
                        <ProfileAvatar size={70} />
                    </div>

                    <div className="mypage-name text-heading-3">{user.nickname}</div>

                    <div className="mypage-sub text-caption">
                        가입일:{" "}
                        {new Date(user.createdAt).toLocaleDateString("ko-KR", {
                            year: "numeric",
                            month: "2-digit",
                            day: "2-digit",
                        })}
                    </div>
                    <div className="mypage-sub text-caption">
                        인증한 동네: {user.location}
                    </div>
                </div>

                <div className="mypage-stats">
                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">2</div>
                        </div>
                        <div className="mypage-stat-label text-caption">판매중</div>
                    </div>

                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">5</div>
                        </div>
                        <div className="mypage-stat-label text-caption">거래완료</div>
                    </div>

                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">12</div>
                        </div>
                        <div className="mypage-stat-label text-caption">구매</div>
                    </div>
                </div>

                <div className="mypage-menu">
                    <button
                        className="mypage-menu-item"
                        onClick={() => navigate("/profile-view")}
                    >
                        <span className="mypage-menu-left">
                            <img src={userIcon} alt="" className="mypage-menu-icon" />
                            <span className="mypage-menu-text">내 프로필 보기</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button className="mypage-menu-item">
                        <span className="mypage-menu-left">
                            <img src={wrenchIcon} alt="" className="mypage-menu-icon" />
                            <span className="mypage-menu-text">계정 설정/수정</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button
                        className="mypage-menu-item"
                        onClick={() => navigate("/NeighborhoodManage")}
                    >
                        <span className="mypage-menu-left">
                            <img src={locationIcon} alt="" className="mypage-menu-icon" />
                            <span className="mypage-menu-text">동네 인증 관리</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button className="mypage-menu-item">
                        <span className="mypage-menu-left">
                            <img src={packageIcon} alt="" className="mypage-menu-icon" />
                            <span className="mypage-menu-text">고객 지원</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>
                </div>
            </div>

            <button className="mypage-logout" type="button" onClick={handleLogout}>
                로그아웃
            </button>
        </div>
    );
}