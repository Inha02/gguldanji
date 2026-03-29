import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { COLORS } from "../constants/colors";
import { CATEGORY_ITEMS } from "../constants/categories";

const steps = [
    {
        title: "곰곰이와 함께하는 중고거래",
        description: "가격부터 거래 대화 분석까지,\n똑똑한 에이전트 곰곰이가 도와줘요",
        type: "intro1",
        buttonText: "다음",
    },
    {
        title: "가격 고민, 곰곰이가 덜어드려요",
        description:
            "거래 데이터를 바탕으로 합리적인 가격을 알려줘요\n판매자와 구매자,\n모두에게 알맞은 가격을 확인해 보세요",
        type: "intro2",
        buttonText: "다음",
    },
    {
        title: "대화도, 거래도 더 안전하게",
        description:
            "응답 속도와 대화 패턴을 분석해\n판매자의 성향을 미리 파악할 수 있어요",
        type: "intro3",
        buttonText: "다음",
    },
    {
        title: "관심 있는 물건을 골라주세요",
        description: "곰곰이가 취향에 맞는 상품을 추천해드릴게요",
        type: "category",
        buttonText: "다음",
    },
    {
        title: "좋은 물건과 인연이\n달콤하게 모이는 곳, 꿀단지",
        description: "내 동네를 설정하고\n꿀단지를 시작해보세요",
        type: "start",
        buttonText: "시작하기",
    },
];

export default function Onboarding() {
    const navigate = useNavigate();
    const [step, setStep] = useState(0);
    const [selectedCategories, setSelectedCategories] = useState([
        "여성의류",
        "패션잡화",
        "뷰티/미용",
    ]);

    const current = steps[step];

    const toggleCategory = (name) => {
        setSelectedCategories((prev) =>
            prev.includes(name)
                ? prev.filter((item) => item !== name)
                : [...prev, name]
        );
    };

    const handleNext = () => {
        if (step < steps.length - 1) {
            setStep((prev) => prev + 1);
            return;
        }

        localStorage.setItem("onboardingDone", "true");
        localStorage.setItem("selectedCategories", JSON.stringify(selectedCategories));
        navigate("/signup");
    };

    const handleSkip = () => {
        localStorage.setItem("onboardingDone", "true");
        localStorage.setItem("selectedCategories", JSON.stringify(selectedCategories));
        navigate("/signup");
    };

    return (
        <div style={styles.page}>
            {/* Header progress */}
            <div style={styles.header}>
                <div style={styles.progressRow}>
                    {steps.map((_, index) => (
                        <div
                            key={index}
                            style={{
                                ...styles.progressBar,
                                backgroundColor:
                                    index === step ? COLORS.gray400 : COLORS.gray100,
                            }}
                        />
                    ))}
                </div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                {current.type !== "start" && current.type !== "category" && (
                    <>
                        <div style={styles.title}>{current.title}</div>
                        <div style={styles.description}>
                            {current.description.split("\n").map((line, idx) => (
                                <div key={idx}>{line}</div>
                            ))}
                        </div>
                    </>
                )}

                {current.type === "category" && (
                    <>
                        <div style={styles.categoryTopText}>
                            {current.description}
                        </div>
                        <div style={styles.categoryTitle}>{current.title}</div>

                        <div style={styles.categoryGrid}>
                            {CATEGORY_ITEMS.map((item) => {
                                const selected = selectedCategories.includes(item.name);

                                return (
                                    <button
                                        key={item.name}
                                        type="button"
                                        onClick={() => toggleCategory(item.name)}
                                        style={styles.categoryItem}
                                    >
                                        <div style={styles.categoryCircle}>
                                            <img
                                                src={item.icon}
                                                alt={item.name}
                                                style={styles.categoryIcon}
                                            />

                                            {selected && (
                                                <div style={styles.categorySelectedOverlay}>
                                                    <div style={styles.categoryHeart}>♥</div>
                                                </div>
                                            )}
                                        </div>

                                        <div style={styles.categoryLabel}>{item.name}</div>
                                    </button>
                                );
                            })}
                        </div>
                    </>
                )}

                {current.type === "start" && (
                    <div style={styles.startWrap}>
                        <div style={styles.startTitle}>
                            {current.title.split("\n").map((line, idx) => (
                                <div key={idx}>{line}</div>
                            ))}
                        </div>
                        <div style={styles.startDescription}>
                            {current.description.split("\n").map((line, idx) => (
                                <div key={idx}>{line}</div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom buttons */}
            <div style={styles.bottomArea}>
                <button type="button" style={styles.nextBtn} onClick={handleNext}>
                    {current.buttonText}
                </button>

                {current.type !== "start" ? (
                    <button type="button" style={styles.skipBtn} onClick={handleSkip}>
                        건너뛰기
                    </button>
                ) : (
                    <button
                        type="button"
                        style={styles.loginBtn}
                        onClick={() => navigate("/login")}
                    >
                        이미 계정이 있나요? <span style={styles.loginBold}>로그인</span>
                    </button>
                )}
            </div>
        </div>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: COLORS.white,
        position: "relative",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
    },

    header: {
        width: "100%",
        height: 50,
        paddingTop: 28,
        boxSizing: "border-box",
        flexShrink: 0,
    },

    progressRow: {
        width: "100%",
        padding: "0 16px",
        boxSizing: "border-box",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },

    progressBar: {
        width: 64,
        height: 4,
        borderRadius: 4,
    },

    main: {
        flex: 1,
        padding: "30px 16px 0 16px",
        boxSizing: "border-box",
        textAlign: "center",
    },

    title: {
        fontSize: 28,
        lineHeight: "36px",
        fontWeight: 700,
        color: COLORS.black,
        whiteSpace: "pre-line",
    },

    description: {
        marginTop: 16,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.gray600,
        whiteSpace: "pre-line",
    },

    categoryTopText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.gray600,
        marginTop: 8,
    },

    categoryTitle: {
        marginTop: 8,
        fontSize: 28,
        lineHeight: "36px",
        fontWeight: 700,
        color: COLORS.black,
    },

    categoryGrid: {
        marginTop: 36,
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        rowGap: 20,
        columnGap: 8,
        justifyItems: "center",
    },

    categoryItem: {
        border: "none",
        background: "transparent",
        padding: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
        cursor: "pointer",
    },

    categoryCircle: {
        width: 74,
        height: 74,
        borderRadius: "50%",
        backgroundColor: COLORS.gray100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
    },

    categoryIcon: {
        width: 40,
        height: 40,
        objectFit: "contain",
    },

    categoryHeart: {
        width: 24,
        height: 24,
        fontSize: 24,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.white,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },

    categorySelectedOverlay: {
        position: "absolute",
        inset: 0,  
        width: 74,
        height: 74,
        borderRadius: "50%",
        backgroundColor: "rgba(251,226,0,0.9)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },

    categoryLabel: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: COLORS.black,
        textAlign: "center",
        whiteSpace: "nowrap",
    },

    startWrap: {
        marginTop: 120,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
    },

    startTitle: {
        marginTop: 24,
        fontSize: 28,
        lineHeight: "36px",
        fontWeight: 700,
        color: COLORS.black,
        textAlign: "center",
        whiteSpace: "pre-line",
    },

    startDescription: {
        marginTop: 16,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.gray600,
        textAlign: "center",
        whiteSpace: "pre-line",
    },

    bottomArea: {
        position: "absolute",
        left: 16,
        right: 16,
        bottom: 35,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
    },

    nextBtn: {
        width: 358,
        height: 42,
        border: "none",
        borderRadius: 12,
        backgroundColor: COLORS.primary,
        color: COLORS.white,
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",   
        padding: 0,
    },

    skipBtn: {
        marginTop: 10,
        border: "none",
        background: "transparent",
        color: COLORS.black,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        cursor: "pointer",
        textUnderlineOffset: 2,
    },

    loginBtn: {
        marginTop: 10,
        border: "none",
        background: "transparent",
        color: COLORS.gray600,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        cursor: "pointer",
    },

    loginBold: {
        color: COLORS.black,
        fontWeight: 700,
        textDecoration: "underline",
        textUnderlineOffset: 2,
    },
};