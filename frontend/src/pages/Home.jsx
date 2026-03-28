import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import HomeHeader from "../components/HomeHeader";
import HomeBanner from "../components/HomeBanner";
import ProductCard from "../components/ProductCard";
import { getPosts } from "../api/posts";

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

  const selectedCat = searchParams.get("cat");
  const isLoggedIn = !!localStorage.getItem("token");

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  const pageSize = 20;

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const data = await getPosts();
        console.log("GET /posts 응답:", data);

        const normalizedPosts = (
          Array.isArray(data) ? data : data.posts || []
        ).map((item) => ({
          id: item.id || item._id,
          title: item.title || "제목 없음",
          price: String(item.price ?? ""),
          location:
            typeof item.location === "object"
              ? item.location.address || "위치 미정"
              : item.location || item.region || "위치 미정",
          time: item.time || "방금 전",
          tag: item.tag || "적정",
          category: item.category || "기타 중고물품",
          categoryId: item.categoryId || item.category?._id || "",
          description: item.description || "",
          seller: item.seller || null,
        }));

        setPosts(normalizedPosts);
      } catch (error) {
        console.error("게시글 목록 불러오기 실패:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const list = useMemo(() => {
    let data = [...posts];

    if (selectedCat) {
      data = data.filter((x) => x.category === selectedCat);
    }

    if (!isLoggedIn) {
      data = shuffle(data);
    }

    return data;
  }, [posts, isLoggedIn, selectedCat]);

  const totalPages = Math.ceil(list.length / pageSize);

  const paginatedList = useMemo(() => {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return list.slice(start, end);
  }, [list, page]);

  useEffect(() => {
    setPage(1);
  }, [selectedCat]);

  const handleCardClick = (item) => {
    if (!isLoggedIn) {
      setLoginModalOpen(true);
      return;
    }

    navigate(`/product/${item.id}`, {
      state: {
        item: {
          ...item,

          sellerId: item.sellerId
        },
      },
    });
  };

  if (loading) {
    return <div style={{ padding: 16 }}>로딩 중...</div>;
  }

  return (
    <>
      <HomeHeader
        showBell={isLoggedIn}
        onMenuClick={() => navigate("/category")}
        onSearchClick={() => navigate("/search")}
      />

      <div style={styles.page}>
        {isLoggedIn && (
          <>
            <div
              onClick={() => navigate("/recommend")}
              style={{ cursor: "pointer" }}
            >
              <HomeBanner name="송이" />
            </div>
            <div style={{ height: 20 }} />
          </>
        )}

        {!isLoggedIn && <div style={{ height: 10 }} />}

        <div style={styles.grid}>
          {paginatedList.length > 0 ? (
            paginatedList.map((item) => (
              <div
                key={item.id}
                onClick={() => handleCardClick(item)}
                style={{ cursor: "pointer" }}
              >
                <ProductCard item={item} />
              </div>
            ))
          ) : (
            <div style={styles.emptyText}>등록된 게시글이 없습니다.</div>
          )}
        </div>

        {totalPages > 1 && (
          <div style={styles.pagination}>
            <button
              type="button"
              style={{
                ...styles.pageBtn,
                opacity: page === 1 ? 0.4 : 1,
                cursor: page === 1 ? "default" : "pointer",
              }}
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page === 1}
            >
              이전
            </button>

            <span style={styles.pageText}>
              {page} / {totalPages}
            </span>

            <button
              type="button"
              style={{
                ...styles.pageBtn,
                opacity: page === totalPages ? 0.4 : 1,
                cursor: page === totalPages ? "default" : "pointer",
              }}
              onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={page === totalPages}
            >
              다음
            </button>
          </div>
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
  emptyText: {
    gridColumn: "1 / -1",
    fontSize: 16,
    lineHeight: "24px",
    fontWeight: 400,
    color: "#72787F",
    textAlign: "center",
    marginTop: 24,
  },
  pagination: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 12,
    marginTop: 20,
    marginBottom: 12,
  },
  pageBtn: {
    minWidth: 56,
    height: 32,
    border: "none",
    borderRadius: 12,
    backgroundColor: "#E8EBED",
    color: "#262627",
    fontSize: 14,
    lineHeight: "20px",
    fontWeight: 400,
    padding: "0 12px",
  },
  pageText: {
    fontSize: 14,
    lineHeight: "20px",
    fontWeight: 400,
    color: "#262627",
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
};
