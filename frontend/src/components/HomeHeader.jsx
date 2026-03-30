import { useNavigate } from "react-router-dom";
import logo from "../icons/gguldanjiLogo.svg";

export default function HomeHeader({ showBell = true, onMenuClick }) {
    const navigate = useNavigate();

    return (
        <header className="home-header">
            <button className="icon-btn" aria-label="메뉴" onClick={onMenuClick}>
                <HamburgerIcon />
            </button>

            <div style={styles.center}>
                <img src={logo} alt="꿀단지 로고" style={styles.logo} />
            </div>

            <div className="header-right">
                {showBell && (
                    <button
                        className="icon-btn"
                        aria-label="알림"
                        onClick={() => navigate("/notifications")}
                    >
                        <BellIcon />
                    </button>
                )}
                <button
                    className="icon-btn"
                    aria-label="검색"
                    onClick={() => navigate("/search")}
                >
                    <SearchIcon />
                </button>
            </div>
        </header>
    );
}


function HamburgerIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

function BellIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
                d="M18 8a6 6 0 10-12 0c0 7-3 7-3 7h18s-3 0-3-7"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinejoin="round"
            />
            <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

function SearchIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
            <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

const styles = {
    center: {
        position: "absolute",
        left: "50%",
        top: "50%",
        transform: "translate(-50%, -50%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
    },

    logo: {
        height: 24,
        objectFit: "contain",
        display: "block",
        transform: "translateY(5px)",
    },
};