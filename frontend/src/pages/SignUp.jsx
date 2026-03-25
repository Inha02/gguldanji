import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Signup() {
    const navigate = useNavigate();

    const [name, setName] = useState("");
    const [userId, setUserId] = useState("");
    const [password, setPassword] = useState("");
    const [birth, setBirth] = useState("");
    const [gender, setGender] = useState("");
    const [town, setTown] = useState("");

    const handleSignup = (e) => {
        e.preventDefault();
        navigate("/login");
    };

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

                <div style={styles.headerTitle}>회원가입</div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                <div style={styles.welcome}>꿀단지에 오신 것을 환영합니다.</div>

                <form onSubmit={handleSignup} style={styles.form}>
                    {/* 이름 */}
                    <div style={styles.field}>
                        <div style={styles.label}>이름</div>
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="4글자 이내로 입력해주세요."
                            style={styles.input}
                        />
                    </div>

                    {/* 아이디 */}
                    <div style={styles.field}>
                        <div style={styles.label}>아이디</div>
                        <input
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            placeholder="영문, 숫자 포함 8자 이상 입력해주세요."
                            style={styles.input}
                        />
                    </div>

                    {/* 비밀번호 */}
                    <div style={styles.field}>
                        <div style={styles.label}>비밀번호</div>
                        <div style={styles.inputWrap}>
                            <input
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="영문, 숫자 포함 8자 이상 입력해주세요."
                                type="password"
                                style={styles.inputWithIcon}
                            />
                            <button type="button" style={styles.inputIconBtn} aria-label="비밀번호 보기">
                                <EyeIcon />
                            </button>
                        </div>
                    </div>

                    {/* 생년월일 */}
                    <div style={styles.field}>
                        <div style={styles.label}>생년월일</div>
                        <div style={styles.inputWrap}>
                            <input
                                value={birth}
                                onChange={(e) => setBirth(e.target.value)}
                                placeholder="YYYY-MM-DD 형식으로 입력해주세요."
                                style={styles.inputWithIcon}
                            />
                            <button type="button" style={styles.inputIconBtn} aria-label="캘린더">
                                <CalendarIcon />
                            </button>
                        </div>
                    </div>

                    {/* 성별 */}
                    <div style={styles.field}>
                        <div style={styles.label}>성별</div>
                        <div style={styles.genderRow}>
                            <button
                                type="button"
                                onClick={() => setGender("남성")}
                                style={{
                                    ...styles.genderBtn,
                                    ...(gender === "남성" ? styles.genderBtnSelected : styles.genderBtnUnselected),
                                }}
                            >
                                <span
                                    style={{
                                        ...styles.genderText,
                                        color: gender === "남성" ? "#FDFDFD" : "#262627",
                                    }}
                                >
                                    남성
                                </span>
                            </button>

                            <button
                                type="button"
                                onClick={() => setGender("여성")}
                                style={{
                                    ...styles.genderBtn,
                                    ...(gender === "여성" ? styles.genderBtnSelected : styles.genderBtnUnselected),
                                }}
                            >
                                <span
                                    style={{
                                        ...styles.genderText,
                                        color: gender === "여성" ? "#FDFDFD" : "#262627",
                                    }}
                                >
                                    여성
                                </span>
                            </button>
                        </div>
                    </div>

                    {/* 동네 인증 */}
                    <div style={styles.field}>
                        <div style={styles.label}>동네 인증</div>
                        <div style={styles.inputWrap}>
                            <input
                                value={town}
                                onChange={(e) => setTown(e.target.value)}
                                placeholder="동네를 추가해주세요."
                                style={styles.inputWithIcon}
                            />
                            <button type="button" style={styles.plusBoxBtn} aria-label="동네 추가">
                                <PlusIcon />
                            </button>
                        </div>
                    </div>

                    {/* 안내 문구 */}
                    <div style={styles.guideTextWrap}>
                        <div style={styles.guideText}>입력된 정보는 안전하게 보호돼요.</div>
                        <div style={styles.guideText}>
                            가입 후에는 가격 가이드와 안전한 거래를 도와드릴게요.
                        </div>
                    </div>

                    {/* 가입하기 버튼 */}
                    <div style={styles.bottomArea}>
                        <button type="submit" style={styles.submitBtn}>
                            가입하기
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function EyeIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
                d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"
                stroke="#262627"
                strokeWidth="1.8"
            />
            <circle cx="12" cy="12" r="3" stroke="#262627" strokeWidth="1.8" />
        </svg>
    );
}

function CalendarIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="3" y="5" width="18" height="16" rx="3" stroke="#262627" strokeWidth="1.8" />
            <path d="M8 3v4M16 3v4M3 9h18" stroke="#262627" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
    );
}

function PlusIcon() {
    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            {/* 집 모양 선 */}
            <path
                d="M5 10.5L12 5l7 5.5V18a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-7.5Z"
                stroke="#9EA4AA"
                strokeWidth="1.8"
                strokeLinejoin="round"
            />
            {/* 플러스 */}
            <path
                d="M12 9.5v5M9.5 12h5"
                stroke="#9EA4AA"
                strokeWidth="1.8"
                strokeLinecap="round"
            />
        </svg>
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
        padding: "20px 16px 16px 16px",
        boxSizing: "border-box",
        position: "relative",
    },

    welcome: {
        textAlign: "center",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 27,
    },

    form: {
        display: "flex",
        flexDirection: "column",
        minHeight: "100%",
        position: "relative",
    },

    field: {
        marginBottom: 14,
    },

    label: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        marginBottom: 8,
    },

    input: {
        width: "100%",
        height: 42,
        borderRadius: 20,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "0 16px",
        fontSize: 16,
        lineHeight: "24px",
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
    },

    inputWrap: {
        position: "relative",
        width: "100%",
    },

    inputWithIcon: {
        width: "100%",
        height: 42,
        borderRadius: 20,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "0 44px 0 16px",
        fontSize: 16,
        lineHeight: "24px",
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
    },

    inputIconBtn: {
        position: "absolute",
        right: 12,
        top: "50%",
        transform: "translateY(-50%)",
        width: 24,
        height: 24,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    genderRow: {
        display: "flex",
        gap: 8,
    },

    genderBtn: {
        width: 88,
        height: 42,
        borderRadius: 20,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        boxSizing: "border-box",
    },

    genderBtnSelected: {
        backgroundColor: "#FBE200",
        border: "1px solid #C9CDD2",
    },

    genderBtnUnselected: {
        backgroundColor: "#FDFDFD",
        border: "1px solid #C9CDD2",
    },

    genderText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        whiteSpace: "nowrap",
    },

    plusBoxBtn: {
        position: "absolute",
        right: 0,
        top: 0,
        width: 42,
        height: 42,
        borderTopRightRadius: 20,
        borderBottomRightRadius: 20,
        borderTopLeftRadius: 0,
        borderBottomLeftRadius: 0,
        border: "1px solid #C9CDD2",   // gray/200
        borderLeft: "1px solid #C9CDD2",
        backgroundColor: "#E8EBED",    // gray/100
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
        padding: 0,
        boxSizing: "border-box",
    },

    guideTextWrap: {
        marginTop: 107,
        display: "flex",
        flexDirection: "column",
        gap: 4,
        alignItems: "center",
    },

    guideText: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#262627",
        textAlign: "center",
    },

    bottomArea: {
        marginTop: 10,
    },

    submitBtn: {
        width: "100%",
        height: 50,
        borderRadius: 16,
        border: "none",
        backgroundColor: "#FBE200",
        color: "#FFFFFF",
        fontSize: 24,
        lineHeight: "32px",
        fontWeight: 700,
        cursor: "pointer",
    },
};