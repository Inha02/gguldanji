import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import HomeIcon from "../icons/home.svg?react";
import LikeIcon from "../icons/like.svg?react";
import PostIcon from "../icons/post.svg?react";
import ChatIcon from "../icons/chat.svg?react";
import MyPageIcon from "../icons/mypage.svg?react";

export default function BottomNav() {
    const navigate = useNavigate();
    const [loginModalOpen, setLoginModalOpen] = useState(false);

    const isLoggedIn = !!localStorage.getItem("token");

    const handleProtectedClick = (e, to) => {
        if (to === "/") return;

        if (!isLoggedIn) {
            e.preventDefault();
            setLoginModalOpen(true);
        }
    };

    return (
        <>
            <nav className="bottom-nav">
                <NavItem to="/" Icon={HomeIcon} />
                <NavItem
                    to="/likes"
                    Icon={LikeIcon}
                    onProtectedClick={handleProtectedClick}
                />
                <NavItem
                    to="/post"
                    Icon={PostIcon}
                    center
                    onProtectedClick={handleProtectedClick}
                />
                <NavItem
                    to="/chat"
                    Icon={ChatIcon}
                    onProtectedClick={handleProtectedClick}
                />
                <NavItem
                    to="/mypage"
                    Icon={MyPageIcon}
                    onProtectedClick={handleProtectedClick}
                />
            </nav>

            {loginModalOpen && (
                <div
                    style={modalStyles.backdrop}
                    onClick={() => setLoginModalOpen(false)}
                >
                    <div style={modalStyles.modal} onClick={(e) => e.stopPropagation()}>
                        <div style={modalStyles.iconWrap}>
                            <div style={modalStyles.infoIcon}>i</div>
                        </div>

                        <div style={modalStyles.title}>로그인 후 이용 가능합니다.</div>

                        <div style={modalStyles.btnRow}>
                            <button
                                style={{ ...modalStyles.btn, ...modalStyles.btnGhost }}
                                onClick={() => setLoginModalOpen(false)}
                                type="button"
                            >
                                계속 구경하기
                            </button>

                            <button
                                style={{ ...modalStyles.btn, ...modalStyles.btnPrimary }}
                                onClick={() => navigate("/login")}
                                type="button"
                            >
                                로그인 하기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

function NavItem({ to, Icon, center, onProtectedClick }) {
    return (
        <NavLink
            to={to}
            onClick={(e) => onProtectedClick?.(e, to)}
            className={({ isActive }) =>
                `nav-item ${center ? "center" : ""}`
            }
        >
            {({ isActive }) => (
                <Icon
                    className="nav-icon"
                    style={{
                        color: center ? "#FFFFFF" : isActive ? "#000000" : "#9CA3AF",
                    }}
                />
            )}
        </NavLink>
    );
}

const modalStyles = {
    backdrop: {
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.25)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 999,
    },
    modal: {
        width: 300,
        height: 147,
        borderRadius: 12,
        background: "#FDFDFD",
        boxShadow: "0 10px 24px rgba(0,0,0,0.18)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
    },
    iconWrap: {
        marginBottom: 8,
    },
    infoIcon: {
        width: 22,
        height: 22,
        borderRadius: "50%",
        border: "1px solid #C9CDD2",
        color: "#262627",
        display: "grid",
        placeItems: "center",
        fontWeight: 700,
        fontSize: 13,
        lineHeight: "13px",
    },
    title: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 600,
        color: "#262627",
        textAlign: "center",
        marginBottom: 15,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    },
    btnRow: {
        width: "100%",
        display: "flex",
        gap: 10,
    },
    btn: {
        flex: 1,
        height: 36,
        borderRadius: 16,
        border: "none",
        cursor: "pointer",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
    },
    btnPrimary: {
        background: "#FBE200",
        color: "#262627",
    },
    btnGhost: {
        background: "#E8EBED",
        color: "#262627",
    },
};