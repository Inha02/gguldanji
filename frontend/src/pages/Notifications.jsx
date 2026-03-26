import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const notifications = [
    {
        id: 1,
        type: "chat",
        title: "새 메시지가 도착했어요",
        time: "방금 전",
        content: '아이폰 14 Pro • "혹시 오늘 거래 가능할까요?"',
    },
    {
        id: 2,
        type: "trade",
        title: "거래가 완료되었어요",
        time: "10분 전",
        content: "눈송이님과 에어팟 프로 2세대 거래가 완료되었습니다",
    },
    {
        id: 3,
        type: "trade",
        title: "찜한 상품이 판매 완료되었어요",
        time: "26분 전",
        content: "원목 책상이 판매 완료되었어요",
    },
    {
        id: 4,
        type: "trade",
        title: "곰곰이 가격 알림",
        time: "30분 전",
        content: "아이폰 14 Pro의 추천 가격이 업데이트됐어요",
    },
    {
        id: 5,
        type: "chat",
        title: "새 메시지가 도착했어요",
        time: "방금 전",
        content: '아이폰 14 Pro • "혹시 오늘 거래 가능할까요?"',
    },
    {
        id: 6,
        type: "chat",
        title: "새 메시지가 도착했어요",
        time: "방금 전",
        content: '아이폰 14 Pro • "혹시 오늘 거래 가능할까요?"',
    },
];

function NotificationIcon({ type }) {
    if (type === "trade") {
        return (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                    d="M4 8.5L12 4l8 4.5-8 4.5L4 8.5Z"
                    stroke="#262627"
                    strokeWidth="1.8"
                    strokeLinejoin="round"
                />
                <path
                    d="M4 8.5V15.5L12 20l8-4.5V8.5"
                    stroke="#262627"
                    strokeWidth="1.8"
                    strokeLinejoin="round"
                />
            </svg>
        );
    }

    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
                d="M6 18.5L4.5 20V6.5A2.5 2.5 0 0 1 7 4h10a2.5 2.5 0 0 1 2.5 2.5v9A2.5 2.5 0 0 1 17 18H6Z"
                stroke="#262627"
                strokeWidth="1.8"
                strokeLinejoin="round"
            />
            <path
                d="M8 10h.01M12 10h.01M16 10h.01"
                stroke="#262627"
                strokeWidth="2"
                strokeLinecap="round"
            />
        </svg>
    );
}

export default function Notifications() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState("전체");

    const filteredNotifications = useMemo(() => {
        if (activeTab === "전체") return notifications;
        if (activeTab === "거래") return notifications.filter((item) => item.type === "trade");
        if (activeTab === "채팅") return notifications.filter((item) => item.type === "chat");
        return notifications;
    }, [activeTab]);

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <button
                    type="button"
                    aria-label="뒤로가기"
                    style={styles.backBtn}
                    onClick={() => navigate(-1)}
                >
                    <span style={styles.backIcon} />
                </button>

                <div style={styles.headerTitle}>알림</div>
            </div>

            {/* Tabs */}
            <div style={styles.tabRow}>
                {["전체", "거래", "채팅"].map((tab) => (
                    <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        style={{
                            ...styles.tabBtn,
                            ...(activeTab === tab ? styles.tabBtnActive : {}),
                        }}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* List */}
            <div style={styles.list}>
                {filteredNotifications.map((item) => (
                    <div key={item.id} style={styles.item}>
                        <div style={styles.itemInner}>
                            <div style={styles.iconWrap}>
                                <NotificationIcon type={item.type} />
                            </div>

                            <div style={styles.textWrap}>
                                <div style={styles.titleRow}>
                                    <div style={styles.itemTitle}>{item.title}</div>
                                    <div style={styles.itemTime}>{item.time}</div>
                                </div>

                                <div style={styles.itemContent}>{item.content}</div>
                            </div>
                        </div>

                        <div style={styles.divider} />
                    </div>
                ))}
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FDFDFD",
        display: "flex",
        flexDirection: "column",
    },

    header: {
        width: "100%",
        height: 50,
        padding: "13px 16px 0 16px",
        backgroundColor: "#FDFDFD",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        position: "relative",
        flexShrink: 0,
    },

    backBtn: {
        position: "absolute",
        left: 16,
        top: 13,
        width: 24,
        height: 24,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    backIcon: {
        width: 10,
        height: 10,
        display: "block",
        borderLeft: "2px solid #262627",
        borderBottom: "2px solid #262627",
        transform: "rotate(45deg)",
    },

    headerTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
    },

    tabRow: {
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        borderBottom: "1px solid #E8EBED",
        flexShrink: 0,
    },

    tabBtn: {
        height: 42,
        border: "none",
        background: "transparent",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        cursor: "pointer",
        position: "relative",
    },

    tabBtnActive: {
        color: "#FBE200",
        fontWeight: 700,
        borderBottom: "3px solid #FBE200",
    },

    list: {
        flex: 1,
        overflowY: "auto",
        backgroundColor: "#FDFDFD",
    },

    item: {
        width: "100%",
    },

    itemInner: {
        display: "flex",
        alignItems: "flex-start",
        gap: 8,
        padding: "12px 16px 12px 16px",
    },

    iconWrap: {
        width: 24,
        height: 24,
        flexShrink: 0,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
    },

    textWrap: {
        flex: 1,
        minWidth: 0,
    },

    titleRow: {
        display: "flex",
        alignItems: "center",
        gap: 8,
    },

    itemTitle: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 700,
        color: "#262627",
        whiteSpace: "nowrap",
    },

    itemTime: {
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#9EA4AA",
        whiteSpace: "nowrap",
    },

    itemContent: {
        marginTop: 6,
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#262627",
    },

    divider: {
        height: 1,
        backgroundColor: "#E8EBED",
        marginLeft: 16,
        marginRight: 16,
    },
};