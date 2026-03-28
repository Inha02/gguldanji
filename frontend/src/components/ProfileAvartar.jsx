import BearIcon from "../icons/bear.svg?react";

export default function ProfileAvatar({ size = 64 }) {
    return (
        <div
            className="profile-avatar"
            style={{
                width: size,
                height: size,
                borderRadius: "50%",
                backgroundColor: "rgba(251, 226, 0, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
            }}
        >
            <BearIcon
                style={{
                    width: size * 0.55,
                    height: size * 0.55,
                    display: "block",
                }}
            />
        </div>
    );
}