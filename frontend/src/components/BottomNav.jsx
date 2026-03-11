import { NavLink } from "react-router-dom";

export default function BottomNav() {
    return (
        <nav className="bottom-nav">
            <NavItem to="/" label="홈" />
            <NavItem to="/likes" label="찜" />

            {/* 가운데 판매 버튼 */}
            <NavItem to="/post" label="+" center />

            <NavItem to="/chat" label="채팅" />
            <NavItem to="/mypage" label="계정" />
        </nav>
    );
}

function NavItem({ to, label, center }) {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""} ${center ? "center" : ""}`
            }
        >
            {label}
        </NavLink>
    );
}
