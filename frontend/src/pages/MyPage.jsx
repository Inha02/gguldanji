import { useNavigate } from "react-router-dom";

export default function MyPage() {
    const navigate = useNavigate();

    // 목업 데이터
    const user = {
        nickname: "최00",
        joined: "2026년 01월 01일",
        verifiedAreas: "서울: 청파동, 방배1동",
        selling: 8,
        done: 23,
        bought: 34,
    };

    const handleLogout = () => {
        // 로그아웃 로직
        localStorage.removeItem("token")
        navigate("/login");
    };

    return (
        <div className="mypage-page">
            {/* Header */}
            <div className="mypage-header">
                <div className="mypage-title">마이페이지</div>
            </div>

            {/* Main */}
            <div className="mypage-main">
                {/* Profile */}
                <div className="mypage-profile">
                    <div className="mypage-avatar">
                        {/* 기본 프로필: 곰돌이 (임시) */}
                        <div className="mypage-bear" />
                    </div>

                    <div className="mypage-name text-heading-3">{user.nickname}</div>

                    <div className="mypage-sub text-caption">
                        가입일: {user.joined}
                    </div>
                    <div className="mypage-sub text-caption">
                        인증한 동네: {user.verifiedAreas}
                    </div>
                </div>

                {/* Stats */}
                <div className="mypage-stats">
                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">{user.selling}</div>
                        </div>
                        <div className="mypage-stat-label text-caption">판매중</div>
                    </div>

                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">{user.done}</div>
                        </div>
                        <div className="mypage-stat-label text-caption">거래완료</div>
                    </div>

                    <div className="mypage-stat">
                        <div className="mypage-stat-circle">
                            <div className="mypage-stat-num text-heading-3">{user.bought}</div>
                        </div>
                        <div className="mypage-stat-label text-caption">구매</div>
                    </div>
                </div>

                {/* Menu */}
                <div className="mypage-menu">

                    <button
                        className="mypage-menu-item"
                        onClick={() => navigate("/profile-view")}
                    >
                        <span className="mypage-menu-left">
                            <span className="mypage-menu-icon" aria-hidden="true">👤</span>
                            <span className="text-body-1">내 프로필 보기</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button className="mypage-menu-item">
                        <span className="mypage-menu-left">
                            <span className="mypage-menu-icon" aria-hidden="true">🔧</span>
                            <span className="text-body-1">계정 설정/수정</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button
                        className="mypage-menu-item"
                        onClick={() => navigate("/NeighborhoodManage")}
                    >
                        <span className="mypage-menu-left">
                            <span className="mypage-menu-icon" aria-hidden="true">📍</span>
                            <span className="text-body-1">동네 인증 관리</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button className="mypage-menu-item">
                        <span className="mypage-menu-left">
                            <span className="mypage-menu-icon" aria-hidden="true">📦</span>
                            <span className="text-body-1">나의 거래</span>
                        </span>
                        <span className="mypage-menu-arrow" aria-hidden="true" />
                    </button>

                    <button className="mypage-menu-item">
                        <span className="mypage-menu-left">
                            <span className="mypage-menu-icon" aria-hidden="true">🔧</span>
                            <span className="text-body-1">고객 지원</span>
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
