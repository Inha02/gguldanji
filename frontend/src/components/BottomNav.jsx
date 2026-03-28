import { NavLink } from "react-router-dom";
import HomeIcon from "../icons/home.svg?react";
import LikeIcon from "../icons/like.svg?react";
import PostIcon from "../icons/post.svg?react";
import ChatIcon from "../icons/chat.svg?react";
import MyPageIcon from "../icons/mypage.svg?react";

export default function BottomNav() {
    return (
        <nav className="bottom-nav">
            <NavItem to="/" Icon={HomeIcon} />
            <NavItem to="/likes" Icon={LikeIcon} />
            <NavItem to="/post" Icon={PostIcon} center />
            <NavItem to="/chat" Icon={ChatIcon} />
            <NavItem to="/mypage" Icon={MyPageIcon} />
        </nav>
    );
}

function NavItem({ to, Icon, center }) {
    return (
        <NavLink
            to={to}
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