import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function NeighborhoodManage() {
    const navigate = useNavigate();

    const [verifiedTowns, setVerifiedTowns] = useState([
        { id: 1, name: "청파동" },
        { id: 2, name: "방배 1동" },
    ]);

    const handleDeleteTown = (id) => {
        setVerifiedTowns((prev) => prev.filter((town) => town.id !== id));
    };

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

                <div style={styles.headerTitle}>동네 인증 관리</div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                <div style={styles.sectionTitle}>인증 완료된 동네</div>

                <div style={styles.list}>
                    {verifiedTowns.map((town) => (
                        <div key={town.id} style={styles.card}>
                            <div style={styles.cardTop}>
                                <div style={styles.townName}>{town.name}</div>

                                <button
                                    type="button"
                                    style={styles.deleteBtn}
                                    onClick={() => handleDeleteTown(town.id)}
                                >
                                    삭제
                                </button>
                            </div>

                            <div style={styles.mapBox}>
                                <div style={styles.mapPlaceholder} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Bottom Button */}
            <div style={styles.bottomArea}>
                <button type="button" style={styles.addBtn} onClick={()=>navigate("/NeighborhoodAdd")}>
                    동네 추가하기
                </button>
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FDFDFD",
        position: "relative",
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

    main: {
        flex: 1,
        overflowY: "auto",
        padding: "16px 16px 100px 16px",
        boxSizing: "border-box",
    },

    sectionTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 600,
        color: "#262627",
        marginBottom: 12,
    },

    list: {
        display: "flex",
        flexDirection: "column",
        gap: 12,
    },

    card: {
        width: "100%",
        borderRadius: 12,
        backgroundColor: "#FDFDFD",
        border: "1px solid #E8EBED",
        padding: 12,
        boxSizing: "border-box",
    },

    cardTop: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 8,
    },

    townName: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
    },

    deleteBtn: {
        border: "none",
        background: "transparent",
        padding: 0,
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#9EA4AA",
        cursor: "pointer",
    },

    mapBox: {
        width: "100%",
        height: 160,
        borderRadius: 12,
        overflow: "hidden",
        backgroundColor: "#F7F8F9",
    },

    mapPlaceholder: {
        width: "100%",
        height: "100%",
        backgroundColor: "#E8EBED",
    },

    bottomArea: {
        position: "absolute",
        left: 16,
        right: 16,
        bottom: 12,
    },

    addBtn: {
        width: "100%",
        height: 48,
        borderRadius: 16,
        border: "none",
        backgroundColor: "#FBE200",
        color: "#262627",
        fontSize: 20,
        lineHeight: "24px",
        fontWeight: 700,
        cursor: "pointer",
    },
};