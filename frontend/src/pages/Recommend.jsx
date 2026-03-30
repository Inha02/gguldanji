import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeHeader from "../components/HomeHeader";
import ProductCard from "../components/ProductCard";
import { getPosts } from "../api/posts";
import logo from "../icons/gguldanjiLogo.svg";

const CATEGORY_MAP = {
    "7ad5dbd9e4cb3f174a48676d": "디지털기기",
    "e096b92137c6aac44e6b69e0": "가전제품",
    "b5891a53683272fd7b02d933": "패션잡화",
    "05a0a6a562b8853820825d89": "남성의류",
    "c108d56149614671b7d76ae3": "여성의류",
    "141213957cf11e237038eb2a": "스포츠/레저",
    "6f1d2889fd3db21ede53841f": "출산/유아동",
    "e958595973562985419f3935": "취미/게임",
    "607edd254ec6118cd7be5e12": "뷰티/미용",
    "3e2b3eaa856e8a3468392bb9": "반려동물용품",
    "58d89f77218c1f29f69eabb2": "생활용품",
    "d4bbe6c3fec70b3f2fdf161e": "가구/인테리어",
    "b5ae6a87375715947844a78d": "도서",
    "b5cca6912ebc8e8190626d53": "식품",
    "a7833ac47cd87a01f96d6c89": "티켓/교환권",
    "25e9d9b6e4f79a649a28584c": "기타 중고물품",
};

export default function Recommend() {
    const navigate = useNavigate();
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);

    const selectedCategories = useMemo(() => {
        try {
            return JSON.parse(localStorage.getItem("selectedCategories") || "[]");
        } catch (error) {
            console.error("선택 카테고리 파싱 실패:", error);
            return [];
        }
    }, []);

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                const data = await getPosts();
                console.log("GET /posts 응답:", data);

                const rawPosts = Array.isArray(data) ? data : data.posts || [];

                const normalizedPosts = rawPosts.map((item) => {
                    const categoryId = item.categoryId ?? item.category?._id ?? "";
                    const categoryName =
                        CATEGORY_MAP[categoryId] ||
                        item.category?.name ||
                        item.category ||
                        "기타 중고물품";

                    return {
                        id: item.id || item._id,
                        _id: item._id || item.id,
                        title: item.title || "제목 없음",
                        price: String(item.price ?? ""),
                        location:
                            typeof item.location === "object"
                                ? item.location.address || "위치 미정"
                                : item.location || item.region || "위치 미정",
                        time: item.time || "방금 전",
                        tag: item.tag || "적정",
                        category: categoryName,
                        categoryId: categoryId,
                        condition: item.condition || "A급",
                        description: item.description || "",
                        images: Array.isArray(item.images) ? item.images : [],
                        sellerId: item.sellerId || item.seller?._id || item.seller?.id || "",
                        seller: item.seller || null,
                        liked: item.liked || false,
                    };
                });

                setPosts(normalizedPosts);
            } catch (error) {
                console.error("추천 게시글 불러오기 실패:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchPosts();
    }, []);

    const filteredList = useMemo(() => {
        if (selectedCategories.length === 0) return posts;

        return posts.filter((item) =>
            selectedCategories.includes(item.category)
        );
    }, [posts, selectedCategories]);

    const handleCardClick = (item) => {
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
                showBell={true}
                onMenuClick={() => navigate("/category")}
                onSearchClick={() => navigate("/search")}
            />

            <div style={styles.page}>
                <div style={styles.title}>관심 카테고리 추천</div>

                <div style={styles.grid}>
                    {filteredList.length > 0 ? (
                        filteredList.map((item) => (
                            <div
                                key={item.id}
                                onClick={() => handleCardClick(item)}
                                style={{ cursor: "pointer" }}
                            >
                                <ProductCard item={item} />
                            </div>
                        ))
                    ) : (
                        <div style={styles.emptyText}>
                            선택한 카테고리의 게시글이 없습니다.
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

const styles = {
    page: {
        padding: 16,
        backgroundColor: "#F7F8F9",
        minHeight: "100%",
    },
    title: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 16,
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        columnGap: 12,
        rowGap: 10,
    },
    emptyText: {
        gridColumn: "1 / -1",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#72787F",
        textAlign: "center",
        marginTop: 24,
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