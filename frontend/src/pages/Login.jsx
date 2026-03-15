import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getKakaoLoginUrl } from "../api/config";

export default function Login() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const [id, setId] = useState("");
    const [pw, setPw] = useState("");
    // const [loginError, setLoginError] = useState("");

    const token = searchParams.get("token");
    const error = searchParams.get("error");
    const loginError =
        error === "login_failed"
        ? "카카오 로그인에 실패했습니다."
        : "";

    // 카카오 콜백: URL에 ?token= 이 있으면 저장 후 홈으로
    useEffect(() => {
    if (!token) return;

    localStorage.setItem("token", token);
    setSearchParams({});
    navigate("/", { replace: true });

    }, [token, navigate, setSearchParams]);

    const handleLogin = (e) => {
        e.preventDefault();
        // TODO: 백엔드 POST /auth/login 연동 시 교체
        localStorage.setItem("token", "demo-token");
        navigate("/");
    };

    /** 카카오 로그인: 백엔드 /auth/kakao 로 이동 → 카카오 인증 → 백엔드 콜백 → 여기로 리다이렉트(?token=) */
    const handleKakaoLogin = () => {
        window.location.href = getKakaoLoginUrl();
    };

    return (
        <div style={styles.page}>
            {/* ===== Yellow Top Text ===== */}
            <div style={styles.topText}>
                <div style={styles.title}>만나서 반가워요!</div>
                <div style={styles.subTitle}>꿀단지에 로그인하고 내 거래를 이어가세요</div>
            </div>

            {/* ===== White Card (top: 230, 390*614, radius top 40) ===== */}
            <div style={styles.card}>
                <form onSubmit={handleLogin} style={styles.form}>
                    <input
                        value={id}
                        onChange={(e) => setId(e.target.value)}
                        placeholder="아이디"
                        style={styles.input}
                    />

                    <input
                        value={pw}
                        onChange={(e) => setPw(e.target.value)}
                        placeholder="비밀번호"
                        type="password"
                        style={styles.input}
                    />

                    <button type="button" style={styles.findPw}>
                        비밀번호 찾기
                    </button>

                    {loginError ? (
                        <div style={styles.errorText}>{loginError}</div>
                    ) : null}
                    {/* 비밀번호 칸 아래 50 */}
                    <button type="submit" style={styles.loginBtn}>
                        로그인
                    </button>

                    {/* 로그인 버튼 아래 58 */}
                    <div style={styles.orText}>또는</div>

                    {/* 또는 아래 12, 원 58x58, 간격 28 */}
                    <div style={styles.socialRow}>
                        <button type="button" style={{ ...styles.socialBtn, ...styles.naver }}>
                            <span style={styles.naverText}>N</span>
                        </button>

                        <button
                            type="button"
                            style={{ ...styles.socialBtn, ...styles.kakao }}
                            onClick={handleKakaoLogin}
                        >
                            <span style={styles.kakaoText}>TALK</span>
                        </button>
                    </div>

                    <button type="button" style={styles.signup}>
                        회원가입
                    </button>
                </form>
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FBE200", // primary
        position: "relative",
        overflow: "hidden",
    },

    // ✅ 타이틀이 맨윗면으로부터 93
    topText: {
        position: "absolute",
        top: 93,
        left: 20,
        right: 20,
    },

    // Heading1 28/36
    title: {
        fontSize: 28,
        lineHeight: "36px",
        fontWeight: 700,
        color: "#262627",
    },

    // Body1
    subTitle: {
        marginTop: 12,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
    },

    // ✅ 흰색 큰 박스 top이 맨윗면으로부터 230
    card: {
        position: "absolute",
        top: 230,
        left: 0,
        right: 0,
        height: 614, // ✅ 390*614 (폭은 device가 390이라 100%로 OK)
        backgroundColor: "#FDFDFD",
        borderTopLeftRadius: 40,
        borderTopRightRadius: 40,
        padding: "28px 20px 0 20px",
    },

    form: {
        display: "flex",
        flexDirection: "column",
    },

    input: {
        height: 44,
        borderRadius: 30,
        border: "1px solid #E8EBED", // gray/200
        backgroundColor: "#FDFDFD",
        padding: "0 16px",
        outline: "none",
        fontSize: 14,
        lineHeight: "20px",
        color: "#262627",
        marginBottom: 12,
    },

    errorText: {
        marginTop: 8,
        fontSize: 12,
        color: "#c00",
        textAlign: "center",
    },

    findPw: {
        marginTop: -2,
        alignSelf: "flex-end",
        border: "none",
        background: "transparent",
        color: "#262627",
        fontSize: 11,
        lineHeight: "14px",
        cursor: "pointer",
    },

    loginBtn: {
        marginTop: 50, // ✅ 요청
        height: 44,
        borderRadius: 30,
        border: "none",
        backgroundColor: "#FBE200",
        color: "#FDFDFD",
        fontSize: 16, // Body1
        lineHeight: "24px",
        fontWeight: 600,
        cursor: "pointer",
    },

    orText: {
        marginTop: 58, // ✅ 요청
        textAlign: "center",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
    },

    socialRow: {
        marginTop: 12, // ✅ 요청
        display: "flex",
        justifyContent: "center",
        gap: 28, // ✅ 요청
    },

    socialBtn: {
        width: 58,
        height: 58,
        borderRadius: "50%",
        border: "none",
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    // 로고는 나중에 이미지로 교체하면 됨 (지금은 임시)
    naver: { backgroundColor: "#2DB400" },
    naverText: {
        color: "#FDFDFD",
        fontSize: 22,
        lineHeight: "22px",
        fontWeight: 800,
    },

    kakao: { backgroundColor: "#FBE200" },
    kakaoText: {
        color: "#262627",
        fontSize: 12,
        lineHeight: "12px",
        fontWeight: 800,
    },

    signup: {
        marginTop: 56,
        border: "none",
        background: "transparent",
        color: "#262627",
        fontSize: 12,
        lineHeight: "16px",
        cursor: "pointer",
        textAlign: "center",
    },
};