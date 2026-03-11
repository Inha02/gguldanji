import  { useNavigate } from "react-router-dom";
export default function Post() {
    return (
        <div style={styles.page}>
            {/* ===== Header ===== */}
            <div style={styles.header}>
                <button style={styles.backBtn} onClick={() => Navigate("/")} aria-label="뒤로가기">
                    <span style={styles.backIcon} />
                </button>

                <div style={styles.headerTitle}>판매글 작성</div>
            </div>

            {/* ===== Main ===== */}
            <div style={styles.main}>
                {/* 사진 업로드 */}
                <div style={styles.photoBox}>
                    <div style={styles.photoInner}>
                        <div style={styles.cameraIcon} />
                        <div style={styles.photoCount}>0/10</div>
                    </div>
                </div>

                {/* 제목 */}
                <input style={styles.input} placeholder="제목" />

                {/* 카테고리 (일단 입력창 형태로만) */}
                <input style={styles.input} placeholder="카테고리" />

                {/* 자세한 설명 */}
                <div style={styles.sectionLabel}>자세한 설명</div>
                <textarea
                    style={styles.textarea}
                    placeholder="청파동에 올릴 게시글 내용을 작성해주세요."
                />

                {/* 거래 방식 */}
                <div style={styles.sectionLabel}>거래방식</div>
                <div style={styles.tradeRow}>
                    <button style={styles.tradeBtn}>판매하기</button>
                    <button style={styles.tradeBtn}>나눔하기</button>
                </div>

                {/* 가격 입력 */}
                <input style={styles.input} placeholder="가격을 입력해주세요." />

                {/* 가격 가이드 */}
                <div style={styles.guideBox}>
                    <div style={styles.guideTitle}>가격 가이드</div>
                    <div style={styles.guideBody}>
                        <div style={styles.bearIcon} />
                    </div>
                </div>

                {/* (지도/위치 영역은 일단 자리만) */}
                <div style={{ height: 16 }} />
                <div style={styles.mapBox} />
                <button style={styles.addLocationBtn}>위치 추가</button>
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FDFDFD", // honeypot/white
    },

    header: {
        height: 56,
        backgroundColor: "#FDFDFD",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
    },

    backBtn: {
        position: "absolute",
        left: 18,
        width: 36,
        height: 36,
        border: "none",
        background: "transparent",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    // ✅ '<' 모양 제대로 보이게(윗부분 잘림 방지)
    backIcon: {
        width: 10,
        height: 10,
        display: "block",
        borderLeft: "2px solid #1B1D1F",
        borderBottom: "2px solid #1B1D1F",
        transform: "rotate(45deg)",
        marginTop: 1,
    },

    headerTitle: {
        fontSize: 20, // honeypot/Heading3 = 20/28
        lineHeight: "28px",
        fontWeight: 600,
        color: "#1B1D1F",
    },

    main: {
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 12,
    },

    // 사진 업로드 박스
    photoBox: {
        width: 72,
        height: 72,
        borderRadius: 12,
        backgroundColor: "#E8EBED", // honeypot/gray/100
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
    photoInner: {
        width: "100%",
        height: "100%",
        borderRadius: 12,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
    },
    cameraIcon: {
        width: 18,
        height: 14,
        border: "2px solid #72787F",
        borderRadius: 3,
        position: "relative",
    },
    photoCount: {
        fontSize: 11, // text-small
        lineHeight: "14px",
        color: "#72787F",
    },

    input: {
        height: 40,
        borderRadius: 8,
        border: "1px solid #C9CDD2", // gray/200 정도로 입력 테두리 느낌
        padding: "0 12px",
        outline: "none",
        fontSize: 14, // Body2
        lineHeight: "20px",
        color: "#1B1D1F",
        backgroundColor: "#FDFDFD",
    },

    sectionLabel: {
        fontSize: 12, // Caption
        lineHeight: "16px",
        fontWeight: 400,
        color: "#454C53", // gray/600
        marginTop: 4,
    },

    textarea: {
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        padding: 12,
        outline: "none",
        minHeight: 110,
        resize: "none",
        fontSize: 14,
        lineHeight: "20px",
        color: "#1B1D1F",
        backgroundColor: "#FDFDFD",
    },

    // 거래방식 버튼(요구사항)
    tradeRow: {
        display: "flex",
        gap: 10,
    },
    tradeBtn: {
        flex: 1,
        height: 36,
        borderRadius: 4,              // ✅ 모서리반경 4
        border: "1px solid #72787F",  // ✅ gray/500
        backgroundColor: "#F7F8F9",   // ✅ gray/50
        fontSize: 14,                 // Body2 정도
        lineHeight: "20px",
        color: "#1B1D1F",
        cursor: "pointer",
    },

    // 가격 가이드 박스(요구사항)
    guideBox: {
        borderRadius: 12,
        backgroundColor: "#F7F8F9",   // ✅ gray/50
        border: "1px solid #9EA4AA",  // ✅ gray/400
        padding: 12,
    },
    guideTitle: {
        fontSize: 12, // Caption
        lineHeight: "16px",
        color: "#454C53",
        marginBottom: 10,
    },
    guideBody: {
        height: 64,
        display: "flex",
        alignItems: "center",
    },
    bearIcon: {
        width: 44,
        height: 44,
        borderRadius: "50%",
        backgroundColor: "#E8EBED",
    },

    // 지도/위치 자리
    mapBox: {
        height: 120,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
    },
    addLocationBtn: {
        width: 90,
        height: 28,
        borderRadius: 6,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        fontSize: 12,
        lineHeight: "16px",
        color: "#454C53",
        cursor: "pointer",
    },
};
