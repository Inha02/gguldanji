import { useNavigate } from "react-router-dom";
import logo from "../icons/gguldanjiLogo.svg";
import menuIcon from "../icons/mynaui_menu.svg";
import bellIcon from "../icons/mynaui_bell.svg";
import searchIcon from "../icons/mynaui_search.svg";

export default function HomeHeader({ showBell = true, onMenuClick }) {
    const navigate = useNavigate();

    return (
        <header className="home-header">
            <button className="icon-btn" aria-label="메뉴" onClick={onMenuClick}>
                <img src={menuIcon} alt="메뉴" style={styles.icon} />
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
                        <img src={bellIcon} alt="알림" style={styles.icon} />
                    </button>
                )}
                <button
                    className="icon-btn"
                    aria-label="검색"
                    onClick={() => navigate("/search")}
                >
                    <img src={searchIcon} alt="검색" style={styles.icon} />
                </button>
            </div>
        </header>
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
        transform: "translateY(3px)",
    },

    icon: {
        width: 24,
        height: 24,
        display: "block",
        transform: "translateY(-10px)",
        }
};