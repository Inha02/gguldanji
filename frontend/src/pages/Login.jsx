import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import kakaoIcon from "../icons/kakao_talk.svg";

export default function Login() {
    const navigate = useNavigate();
    const [id, setId] = useState("");
    const [pw, setPw] = useState("");
    const [searchParams] = useSearchParams();

    useEffect(() => {
        const token = searchParams.get("token");

        if (token) {
            console.log("카카오 토큰:", token);

            localStorage.setItem("token", token);

            navigate("/", { replace: true });
        }
    }, [searchParams, navigate]);

    const handleLogin = async (e) => {
    e.preventDefault();
    
    try {
        const res = await fetch("http://localhost:4000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email: id,   // ⭐ id → email로 맞추세요 (백엔드 기준)
                password: pw,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.message || "로그인 실패");
            return;
        }

        // ⭐ 핵심
        const token = data.token;
        localStorage.setItem("token", token);

        navigate("/");
    } catch (err) {
        console.error(err);
        alert("서버 오류");
    }
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

                    {/* 비밀번호 칸 아래 50 */}
                    <button type="submit" style={styles.loginBtn}>
                        로그인
                    </button>

                    {/* 로그인 버튼 아래 58 */}
                    <div style={styles.orText}>또는</div>

                    {/* 또는 아래 12, 원 58x58, 간격 28 */}
                    <div style={styles.socialRow}>
                        <button 
                        type="button" style={{ ...styles.socialBtn, ...styles.kakao }} onClick={() => {
        window.location.href = "http://localhost:4000/auth/kakao";
    }}>
    <img 
        src={kakaoIcon} alt="카카오 로그인" style={styles.kakaoIcon} />
                        </button>
                    </div>

                    <button type="button" style={styles.signup} onClick={() => navigate("/onboarding")}>
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
        bottom: 0, 
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

    findPw: {
        marginTop: -2,
        alignSelf: "flex-end",
        border: "none",
        background: "transparent",
        color: "#262627",
        fontSize: 14,          
        lineHeight: "20px",
        fontWeight: 400,
        cursor: "pointer",
        textDecoration: "underline",
        textUnderlineOffset: 2,
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
        marginTop: 58,
        textAlign: "center",
        fontSize: 16,          // Body1
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
        display: "flex",
        placeItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        padding: 0,
    },

    kakao: { backgroundColor: "#FBE200" },
    kakaoIcon: {
        width: 29,
        height: 29,
        objectFit:"contain",
    },

    signup: {
        position: "absolute",
        left: "50%",
        bottom: 38,           
        transform: "translateX(-50%)",
        border: "none",
        background: "transparent",
        color: "#262627",
        fontSize: 16,          
        lineHeight: "24px",
        fontWeight: 400,
        cursor: "pointer",
        textDecoration: "underline",
        textUnderlineOffset: 2,
    },
};