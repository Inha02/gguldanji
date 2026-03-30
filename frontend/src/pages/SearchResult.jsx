import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { COLORS } from "../constants/colors";
import HomeHeader from "../components/HomeHeader";
import ProductCard from "../components/ProductCard";
import { getPosts } from "../api/posts";
import logo from "../icons/gguldanjiLogo.svg";

export default function SearchResult() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const keyword = (searchParams.get("q") || "").trim();
    const isLoggedIn = !!localStorage.getItem("token");

    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loginModalOpen, setLoginModalOpen] = useState(false);

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                const data = await getPosts();
                console.log("GET /posts 응답:", data);

                const normalizedPosts = (
                    Array.isArray(data) ? data : data.posts || []
                ).map((item) => ({
                    id: item.id || item._id,
                    _id: item._id || item.id,
                    title: item.title || "제목 없음",
                    price: item.price
                        ? Number(String(item.price).replace(/,/g, "")).toLocaleString("ko-KR")
                        : "",
                    location:
                        typeof item.location === "object"
                            ? item.location.address || "위치 미정"
                            : item.location || item.region || "위치 미정",
                    time: item.time || "방금 전",
                    tag: item.tag || "적정",
                    category: item.category?.name || item.category || "기타 중고물품",
                    categoryId: item.categoryId || item.category?._id || "",
                    description: item.description || "",
                    images: Array.isArray(item.images) ? item.images : [],
                    sellerId: item.sellerId || item.seller?._id || item.seller?.id || "",
                    seller: item.seller || null,
                    liked: item.liked || false,
                }));

                setPosts(normalizedPosts);
            } catch (error) {
                console.error("검색 결과 불러오기 실패:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchPosts();
    }, []);

    const filteredPosts = useMemo(() => {
        if (!keyword) return [];

        const lowerKeyword = keyword.toLowerCase();

        return posts.filter((item) => {
            const title = item.title?.toLowerCase() || "";
            const description = item.description?.toLowerCase() || "";
            const category = item.category?.toLowerCase() || "";

            return (
                title.includes(lowerKeyword) ||
                description.includes(lowerKeyword) ||
                category.includes(lowerKeyword)
            );
        });
    }, [posts, keyword]);

    const handleCardClick = (item) => {
        if (!isLoggedIn) {
            setLoginModalOpen(true);
            return;
        }

        navigate(`/product/${item.id}`, {
            state: {
                item: {
                    ...item,
                    sellerId: item.sellerId,
                },
            },
        });
    };
    
      if (loading) {
        return (
          <div style={styles.loadingContainer}>
            <img src={logo} alt="꿀단지 로고" style={styles.loadingLogo} />
            <div style={styles.loadingText}>잠시만 기다려주세요</div>
          </div>
        )
      }
    return (
        <>
            <HomeHeader
                showBell={isLoggedIn}
                onMenuClick={() => navigate("/category")}
                onSearchClick={() => navigate("/search")}
            />

            <div style={styles.page}>
                <div style={styles.resultText}>
                    ‘{keyword}’에 대한 검색 결과
                </div>

                {filteredPosts.length > 0 ? (
                    <div style={styles.grid}>
                        {filteredPosts.map((item) => (
                            <div
                                key={item.id}
                                onClick={() => handleCardClick(item)}
                                style={{ cursor: "pointer" }}
                            >
                                <ProductCard item={item} />
                            </div>
                        ))}
                    </div>
                ) : (
                    <div style={styles.emptyText}>검색 결과가 없습니다.</div>
                )}
            </div>

            {loginModalOpen && (
                <div
                    style={modalStyles.backdrop}
                    onClick={() => setLoginModalOpen(false)}
                >
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
        padding: "8px 16px 16px 16px",
        backgroundColor: "#F7F8F9",
        minHeight: "100%",
        boxSizing: "border-box",
    },
    resultText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
        marginBottom: 8,
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        columnGap: 12,
        rowGap: 10,
    },
    emptyText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.gray500,
        textAlign: "center",
        marginTop: 24,
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
        color: "#262627",
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
        color: "#262627",
        textAlign: "center",
        marginBottom: 15,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
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

    loadingContainer: {
        width: "100%",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
        backgroundColor: "#F7F8F9",
    },

    loadingLogo: {
        width: 80,
        height: "auto",
    },

    loadingText: {
        fontSize: 14, // Body2 기준
        lineHeight: "20px",
        fontWeight: 400,
        color: "#262627",
    },
};