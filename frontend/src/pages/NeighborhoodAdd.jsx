import { useNavigate } from "react-router-dom";

export default function NeighborhoodAdd() {
    const navigate = useNavigate();

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <button
                    type="button"
                    aria-label="뒤로가기"
                    style={styles.backBtn}
                    onClick={() => navigate("/neighborhoodmanage")}
                >
                    <span style={styles.backIcon} />
                </button>

                <div style={styles.headerTitle}>동네 인증 관리</div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                <div style={styles.sectionTitle}>현위치</div>

                <div style={styles.mapBox}>
                    <div style={styles.mapPlaceholder} />
                </div>

                <div style={styles.locationText}>
                    현재 위치는 <span style={styles.locationTown}>방배 2동</span>이에요.
                </div>
            </div>

            {/* Bottom Button */}
            <div style={styles.bottomArea}>
                <button type="button" style={styles.addBtn}>
                    현재 위치로 동네 인증하기
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
        padding: "16px 0 100px 0",
        boxSizing: "border-box",
    },

    sectionTitle: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 700,
        color: "#262627",
        padding: "0 16px",
        marginBottom: 12,
    },

    mapBox: {
        width: "100%",
        height: 270,
        backgroundColor: "#F7F8F9",
        overflow: "hidden",
    },

    mapPlaceholder: {
        width: "100%",
        height: "100%",
        backgroundColor: "#E8EBED",
    },

    locationText: {
        marginTop: 16,
        textAlign: "center",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
    },

    locationTown: {
        fontWeight: 700,
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
        lineHeight: "28px",
        fontWeight: 700,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },
};