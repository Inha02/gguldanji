import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ProfileAvatar from "../components/ProfileAvartar";

const soldItems = [
    { id: 1 },
    { id: 2 },
    { id: 3 },
    { id: 4 },
];

const reviewTags = ["#친절해요", "#설명이 자세해요", "#네고왕"];

const motivationData = [
    { label: "가격 민감도", value: 90 },
    { label: "효율 지향", value: 45 },
    { label: "거래 즐김", value: 68 },
    { label: "협상 유연성", value: 90 },
];

const communicationData = [
    { label: "응답 패턴", value: 90 },
    { label: "정보 제공", value: 45 },
    { label: "친근함", value: 68 },
    { label: "설명 명확도", value: 90 },
];

const trustData = [
    { label: "제품 설명", value: 90 },
    { label: "거래 투명성", value: 45 },
    { label: "문제 대응", value: 68 },
];

function TraitBarSection({ title, titleColor, data, fillColor }) {
    return (
        <div style={styles.traitSection}>
            <div style={{ ...styles.traitTitle, color: titleColor }}>{title}</div>

            <div style={styles.traitList}>
                {data.map((item) => (
                    <div key={item.label} style={styles.traitRow}>
                        <div style={styles.traitLabel}>{item.label}</div>

                        <div style={styles.traitBarWrap}>
                            <div style={styles.traitBarBg}>
                                <div
                                    style={{
                                        ...styles.traitBarFill,
                                        width: `${item.value}%`,
                                        backgroundColor: fillColor,
                                    }}
                                />
                            </div>
                        </div>

                        <div style={styles.traitValue}>{item.value}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function ProfileView() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState("거래");

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <button
                    type="button"
                    aria-label="뒤로가기"
                    style={styles.backBtn}
                    onClick={() => navigate("/mypage")}
                >
                    <span style={styles.backIcon} />
                </button>

                <div style={styles.headerTitle}>나의 프로필</div>

                <div style={styles.headerRight}>
                    <button type="button" aria-label="공유" style={styles.iconBtn}>
                        <span style={styles.shareIcon}>↥</span>
                    </button>

                    <button type="button" aria-label="메뉴" style={styles.iconBtn}>
                        <span style={styles.kebabDots} />
                    </button>
                </div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                {/* Profile Top */}
                <div style={styles.profileTop}>
                        <ProfileAvatar size={50} />

                    <div style={styles.profileInfo}>
                        <div style={styles.name}>최00</div>
                        <div style={styles.subText}>가입일: 2026년 01월 01일</div>
                        <div style={styles.subText}>인증한 동네: 청파동, 방배1동</div>
                    </div>
                </div>

                {/* Tabs */}
                <div style={styles.tabRow}>
                    <button
                        type="button"
                        onClick={() => setActiveTab("거래")}
                        style={{
                            ...styles.tabBtn,
                            ...(activeTab === "거래" ? styles.tabBtnActive : {}),
                        }}
                    >
                        거래
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab("판매 성향")}
                        style={{
                            ...styles.tabBtn,
                            ...(activeTab === "판매 성향" ? styles.tabBtnActive : {}),
                        }}
                    >
                        판매 성향
                    </button>
                </div>

                {/* 거래 탭 */}
                {activeTab === "거래" && (
                    <div style={styles.section}>
                        <div style={styles.sectionTitle}>최근 거래 요약</div>

                        <div style={styles.sectionSubTitle}>최근 판매한 상품 리스트</div>

                        <div style={styles.soldList}>
                            {soldItems.map((item) => (
                                <div key={item.id} style={styles.soldItem} />
                            ))}
                        </div>

                        <div style={styles.keywordTitle}>후기 키워드 태그</div>

                        <div style={styles.tagList}>
                            {reviewTags.map((tag) => (
                                <div key={tag} style={styles.tagItem}>
                                    {tag}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 판매 성향 탭 */}
                {activeTab === "판매 성향" && (
                    <div style={styles.section}>
                        <div style={styles.summaryBox}>
                            가격 민감도가 높고 효율적 거래를 선호하는 판매자 입니다.
                            <br />
                            정보 제공이 명확합니다.
                        </div>

                        <TraitBarSection
                            title="거래 동기"
                            titleColor="#FF8D28"
                            data={motivationData}
                            fillColor="rgba(255, 141, 40, 0.6)"
                        />

                        <TraitBarSection
                            title="커뮤니케이션 스타일"
                            titleColor="#2699E9"
                            data={communicationData}
                            fillColor="rgba(38, 153, 233, 0.6)"
                        />

                        <TraitBarSection
                            title="신뢰 구축"
                            titleColor="#93C572"
                            data={trustData}
                            fillColor="rgba(147, 197, 114, 0.6)"
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FDFDFD",
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

    headerRight: {
        position: "absolute",
        right: 16,
        top: 13,
        display: "flex",
        alignItems: "center",
        gap: 8,
    },

    iconBtn: {
        width: 24,
        height: 24,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    shareIcon: {
        fontSize: 16,
        lineHeight: "16px",
        color: "#262627",
        transform: "translateY(-1px)",
    },

    kebabDots: {
        width: 3,
        height: 3,
        borderRadius: "50%",
        backgroundColor: "#262627",
        boxShadow: "0 -6px 0 #262627, 0 6px 0 #262627",
    },

    main: {
        padding: "16px 16px 24px 16px",
    },

    profileTop: {
        display: "flex",
        alignItems: "center",
        gap: 16,
    },

    profileInfo: {
        display: "flex",
        flexDirection: "column",
        gap: 4,
    },

    name: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 600,
        color: "#262627",
    },

    subText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#72787F",
    },

    tabRow: {
        marginTop: 20,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        borderBottom: "1px solid #E8EBED",
    },

    tabBtn: {
        height: 44,
        border: "none",
        background: "transparent",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 600,
        color: "#262627",
        cursor: "pointer",
        position: "relative",
    },

    tabBtnActive: {
        color: "#FBE200",
        borderBottom: "3px solid #FBE200",
    },

    section: {
        marginTop: 20,
    },

    sectionTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 8,
    },

    sectionSubTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#262627",
        marginBottom: 12,
    },

    soldList: {
        display: "flex",
        gap: 12,
        overflowX: "auto",
        paddingBottom: 4,
        marginBottom: 24,
    },

    soldItem: {
        width: 100,
        height: 100,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
        flexShrink: 0,
    },

    keywordTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 12,
    },

    tagList: {
        display: "flex",
        gap: 8,
        flexWrap: "wrap",
    },
    
    tagItem: {
        height: 28,
        padding: "0 12px",
        borderRadius: 20,
        backgroundColor: "rgba(251, 226, 0, 0.3)",
        border: "1px solid #FBE200",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 500,
        color: "#262627",
        whiteSpace: "nowrap",
        boxSizing: "border-box",
    },

    summaryBox: {
        width: "100%",
        maxWidth: 358,
        minHeight: 52,
        borderRadius: 12,
        backgroundColor: "#F7F8F9",
        padding: "10px 12px",
        boxSizing: "border-box",
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#262627",
        marginBottom: 20,
    },

    traitSection: {
        marginBottom: 20,
    },

    traitTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 600,
        marginBottom: 8,
    },

    traitList: {
        display: "flex",
        flexDirection: "column",
        gap: 8,
    },

    traitRow: {
        display: "grid",
        gridTemplateColumns: "52px 1fr 24px",
        alignItems: "center",
        columnGap: 8,
    },

    traitLabel: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#262627",
    },

    traitBarWrap: {
        display: "flex",
        alignItems: "center",
    },

    traitBarBg: {
        width: "100%",
        height: 12,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
        overflow: "hidden",
    },

    traitBarFill: {
        height: "100%",
        borderRadius: 12,
    },

    traitValue: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#72787F",
        textAlign: "right",
    },
};