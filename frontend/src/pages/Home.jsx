import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import HomeHeader from "../components/HomeHeader";
import HomeBanner from "../components/HomeBanner";
import ProductCard from "../components/ProductCard";

const mock = [
    { id: 1, title: "아이폰 14 Pro 256GB", price: "950,000", location: "서울 강남구", time: "2시간 전", tag: "저가", category: "디지털기기" },
    { id: 2, title: "에어팟 프로 2세대(정품)", price: "210,000", location: "서울 서초구", time: "3시간 전", tag: "저가", category: "디지털기기" },
    { id: 3, title: "이케아 스탠드 조명", price: "15,000", location: "서울 강남구", time: "4시간 전", tag: "상가", category: "가구/인테리어" },
    { id: 4, title: "원목 책상", price: "40,000", location: "서울 강남구", time: "7시간 전", tag: "적정", category: "가구/인테리어" },
    { id: 5, title: "검은 색 니트 조끼", price: "30,000", location: "서울 강남구", time: "8시간 전", tag: "적정", category: "여성의류" },
    { id: 6, title: "검은 색 나이키 신발", price: "90,000", location: "서울 서초구", time: "11시간 전", tag: "상가", category: "패션잡화" },
];

function shuffle(arr) {
    const copy = [...arr];
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
}

export default function Home() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    // URL에서 선택된 카테고리 읽기
    const selectedCat = searchParams.get("cat");

    // 임시 로그인 판별
    const isLoggedIn = !!localStorage.getItem("token");

    // 카테고리 필터 + 로그인 전 랜덤
    const list = useMemo(() => {
        let data = [...mock];

        // 카테고리 선택되었으면 필터
        if (selectedCat) {
            data = data.filter((x) => x.category === selectedCat);
        }

        // 로그인 전에는 랜덤
        if (!isLoggedIn) {
            data = shuffle(data);
        }

        return data;
    }, [isLoggedIn, selectedCat]);

    const [loginModalOpen, setLoginModalOpen] = useState(false);

    const handleCardClick = () => {
        if (!isLoggedIn) {
            setLoginModalOpen(true);
            return;
        }
        // 로그인 후 카드 클릭 동작은 연결 예정
    };

    return (
        <>
            {/* 로그인 전: 알림 버튼 숨김 + 햄버거 버튼은 카테고리로 이동 */}
            <HomeHeader showBell={isLoggedIn} onMenuClick={() => navigate("/category")} />

            <div style={styles.page}>
                {/* 로그인 후에만 배너 노출 */}
                {isLoggedIn && (
                    <>
                        <HomeBanner name="송이" />
                        <div style={{ height: 20 }} />
                    </>
                )}

                {!isLoggedIn && <div style={{ height: 10 }} />}

                <div style={styles.grid}>
                    {list.map((item) => (
                        <div key={item.id} onClick={handleCardClick} style={{ cursor: "pointer" }}>
                            <ProductCard item={item} />
                        </div>
                    ))}
                </div>
            </div>

            {/* 로그인 유도 모달창 */}
            {loginModalOpen && (
                <div style={modalStyles.backdrop} onClick={() => setLoginModalOpen(false)}>
                    <div style={modalStyles.modal} onClick={(e) => e.stopPropagation()}>
                        <div style={modalStyles.iconWrap}>
                            <div style={modalStyles.infoIcon}>i</div>
                        </div>

                        <div style={modalStyles.title}>로그인 후 이용 가능합니다.</div>

                        <div style={modalStyles.btnRow}>
                            <button
                                style={{ ...modalStyles.btn, ...modalStyles.btnGhost }}
                                onClick={() => setLoginModalOpen(false)}
                                type="button"
                            >
                                계속 구경하기
                            </button>

                            <button
                                style={{ ...modalStyles.btn, ...modalStyles.btnPrimary }}
                                onClick={() => navigate("/login")}
                                type="button"
                            >
                                로그인 하기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

const styles = {
    page: {
        padding: 16,
        backgroundColor: "#F7F8F9",
        minHeight: "100%",
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        columnGap: 12,
        rowGap: 10,
    },
};

const modalStyles = {
    backdrop: {
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.25)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 999,
    },
    modal: {
        width: 300,
        height: 147,
        borderRadius: 12,
        background: "#FDFDFD",
        boxShadow: "0 10px 24px rgba(0,0,0,0.18)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
    },
    iconWrap: {
        marginBottom: 8,
    },
    infoIcon: {
        width: 22,
        height: 22,
        borderRadius: "50%",
        border: "1px solid #C9CDD2",
        color: "#1B1D1F",
        display: "grid",
        placeItems: "center",
        fontWeight: 700,
        fontSize: 13,
        lineHeight: "13px",
    },
    title: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 600,
        color: "#1B1D1F",
        textAlign: "center",
        marginBottom: 15,
    },
    btnRow: {
        width: "100%",
        display: "flex",
        gap: 10,
    },
    btn: {
        flex: 1,
        height: 36,
        borderRadius: 16,
        border: "none",
        cursor: "pointer",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
    },
    btnPrimary: {
        background: "#FBE200",
        color: "#262627",
    },
    btnGhost: {
        background: "#E8EBED",
        color: "#262627",
    },
};