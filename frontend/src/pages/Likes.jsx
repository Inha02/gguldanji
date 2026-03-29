import { useMemo, useState, useEffect } from "react";

/*
const mockLikes = [
    { id: 1, title: "아이폰 14 Pro 256GB", price: "950,000", location: "서울 강남구", time: "2시간 전", tag: "저가", done: false },
    { id: 2, title: "에어팟 프로 2세대(정품)", price: "210,000", location: "서울 서초구", time: "3시간 전", tag: "저가", done: true },
    { id: 3, title: "이케아 스탠드 조명", price: "15,000", location: "서울 강남구", time: "4시간 전", tag: "상가", done: false },
    { id: 4, title: "원목 책상", price: "40,000", location: "서울 강남구", time: "7시간 전", tag: "적정", done: false },
    { id: 5, title: "검은 색 니트 조끼", price: "30,000", location: "서울 강남구", time: "8시간 전", tag: "적정", done: false },
    { id: 6, title: "검은 색 나이키 신발", price: "90,000", location: "서울 서초구", time: "11시간 전", tag: "상가", done: false },
];
*/

function LikeImageCard({ item, liked, onToggleLike }) {
  const label = item.done ? "거래완료" : item.tag;

  const tagStyleMap = {
    저가: "#93C572",
    상가: "#FF6666",
    적정: "#2699E9",
    거래완료: "#262627",
  };

  const tagBg = tagStyleMap[label] || "#262627";

  return (
    <div style={cardStyles.card}>
      <div style={cardStyles.imageArea}>
        {item.images && item.images.length > 0 ? (
  <img
    src={getImageUrl(item.images[0])}
    alt={item.title}
    style={cardStyles.image}
    onError={(e) => {
      e.currentTarget.style.display = "none";
    }}
  />
) : (
  <div style={cardStyles.imagePlaceholder} />
)}

        <div
          style={{
            ...cardStyles.tagBadge,
            backgroundColor: tagBg,
            width: label === "거래완료" ? 54 : 33,
          }}
        >
          {label}
        </div>

        <button
          type="button"
          aria-label="찜"
          onClick={onToggleLike}
          style={cardStyles.heartButton}
        >
          <HeartIcon liked={liked} />
        </button>

        <div style={cardStyles.price}>{item.price}원</div>
      </div>
    </div>
  );
}

function HeartIcon({ liked }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 21s-6.716-4.35-9.193-8.102C.93 10.066 1.38 6.3 4.404 4.78c2.066-1.038 4.466-.46 5.855 1.205L12 7.89l1.741-1.905c1.39-1.665 3.79-2.243 5.855-1.205 3.024 1.52 3.474 5.286 1.597 8.118C18.716 16.65 12 21 12 21z"
        fill={liked ? "#FF2D55" : "#E8EBED"}
        stroke={liked ? "#FF2D55" : "#E8EBED"}
        strokeWidth="1"
      />
    </svg>
  );
}

function getImageUrl(path) {
  if (!path) return "";

  // ✅ 이미 외부 URL (S3 포함)
  if (path.startsWith("http") || path.includes("amazonaws.com")) {
    return path;
  }

  // ✅ 로컬 서버 이미지
  return `http://localhost:4000/${path}`;
}

export default function Likes() {
  const [items, setItems] = useState([]);
  const [excludeDone, setExcludeDone] = useState(false);
  const [sortKey, setSortKey] = useState("최신순");
  const [sortOpen, setSortOpen] = useState(false);
  const [likesState, setLikesState] = useState({});

  const toggleLike = async (id) => {
  try {
    const token = localStorage.getItem("token");

    const res = await fetch("http://localhost:4000/likes/toggle", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        postId: id,
      }),
    });

    const data = await res.json();

    setLikesState((prev) => ({
      ...prev,
      [id]: data.liked,
    }));

  } catch (err) {
    console.error("좋아요 토글 실패:", err);
  }
};

  useEffect(() => {
    const fetchLikes = async () => {
      try {
        const token = localStorage.getItem("token");

        const res = await fetch("http://localhost:4000/likes/my", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        // ⭐ postId 안에 실제 게시글 있음
        const mapped = data.likes.map((like) => {
          const post = like.postId;

          return {
            id: post._id,
            title: post.title,
            price: post.price,
            location: post.location?.address || "지역",
            createdAt: post.createdAt, // ⭐ 이거 추가
            images: post.images || [], 
            time: "방금", // 필요하면 createdAt으로 계산
            tag: "적정",
            done: post.status === "sold",
          };
        });

        setItems(mapped);

        const likeMap = {};
        mapped.forEach((item) => {
          likeMap[item.id] = true;
        });
        setLikesState(likeMap);
      } catch (err) {
        console.error("좋아요 목록 불러오기 실패:", err);
      }
    };

    fetchLikes();
  }, []);

  const list = useMemo(() => {
  let data = [...items];

  if (excludeDone) data = data.filter((x) => !x.done);

  // ✅ 최신순 (createdAt 기준 추천)
  if (sortKey === "최신순") {
    data.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }

  // ✅ 인기순 (나중에 likeCount 쓰면 더 좋음)
  if (sortKey === "인기순") {
    data.sort((a, b) => (b.likeCount || 0) - (a.likeCount || 0));
  }

  // ✅ 저가순
  if (sortKey === "저가순") {
    data.sort((a, b) => Number(a.price) - Number(b.price));
  }

  // ✅ 고가순
  if (sortKey === "고가순") {
    data.sort((a, b) => Number(b.price) - Number(a.price));
  }

  return data;
}, [items, excludeDone, sortKey]); // ⭐ items 추가

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <button
          style={styles.backBtn}
          onClick={() => history.back()}
          aria-label="뒤로가기"
        >
          <span style={styles.backIcon} />
        </button>

        <div style={styles.headerTitle}>찜 목록</div>

        <button style={styles.kebabBtn} aria-label="메뉴" type="button">
          <span style={styles.kebabDots} />
        </button>
      </div>

      <div style={styles.main}>
        <div style={styles.filterRow}>
          <label style={styles.excludeDone}>
            <span style={styles.checkboxWrap}>
              <input
                type="checkbox"
                checked={excludeDone}
                onChange={(e) => setExcludeDone(e.target.checked)}
                style={styles.hiddenCheckbox}
              />
              <span
                style={{
                  ...styles.customCheckbox,
                  ...(excludeDone ? styles.checkedBox : {}),
                }}
              />
            </span>

            <span style={styles.body1}>거래완료 제외</span>
          </label>

          <div style={styles.sortWrap}>
            <button
              style={styles.sortBtn}
              onClick={() => setSortOpen((v) => !v)}
              aria-label="정렬 선택"
              type="button"
            >
              <span style={styles.sortBtnText}>{sortKey}</span>
              <span style={styles.sortIcon}>⭥</span>
            </button>

            {sortOpen && (
              <div style={styles.sortMenu}>
                {["최신순", "인기순", "저가순", "고가순"].map((k) => (
                  <button
                    key={k}
                    style={styles.sortItem}
                    onClick={() => {
                      setSortKey(k);
                      setSortOpen(false);
                    }}
                    type="button"
                  >
                    {k}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={styles.grid}>
          {list.map((item) => (
            <LikeImageCard
              key={item.id}
              item={item}
              liked={!!likesState[item.id]}
              onToggleLike={() => toggleLike(item.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    width: "100%",
    height: "100%",
    backgroundColor: "#FDFDFD",
  },
  header: {
    width: "100%",
    height: 50,
    padding: "13px 16px 0 16px",
    backgroundColor: "#FDFDFD",
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    position: "relative",
  },
  backBtn: {
    width: 24,
    height: 24,
    border: "none",
    background: "transparent",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    padding: 0,
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
    position: "absolute",
    top: 11,
    left: "50%",
    transform: "translateX(-50%)",
    fontSize: 20,
    lineHeight: "28px",
    fontWeight: 600,
    color: "#262627",
  },
  kebabBtn: {
    width: 24,
    height: 24,
    border: "none",
    background: "transparent",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    padding: 0,
  },
  kebabDots: {
    width: 3,
    height: 3,
    borderRadius: "50%",
    backgroundColor: "#262627",
    boxShadow: "0 -6px 0 #262627, 0 6px 0 #262627",
  },
  main: {
    padding: 16,
  },
  filterRow: {
    height: 40,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  excludeDone: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  checkboxWrap: {
    position: "relative",
    width: 20,
    height: 20,
    display: "inline-block",
  },
  hiddenCheckbox: {
    position: "absolute",
    inset: 0,
    opacity: 0,
    cursor: "pointer",
    margin: 0,
  },
  customCheckbox: {
    width: 20,
    height: 20,
    display: "block",
    boxSizing: "border-box",
    borderRadius: 2,
    border: "1px solid #E8EBED",
    backgroundColor: "#FDFDFD",
  },
  checkedBox: {
    backgroundColor: "#FBE200",
    border: "1px solid #FBE200",
  },
  caption: {
    fontSize: 12,
    lineHeight: "16px",
    fontWeight: 400,
    color: "#262627",
  },
  sortWrap: {
    position: "relative",
  },
  sortBtn: {
    border: "none",
    background: "transparent",
    padding: 0,
    display: "flex",
    alignItems: "center",
    gap: 4,
    cursor: "pointer",
  },

  sortBtnText: {
    fontSize: 16,
    lineHeight: "24px",
    fontWeight: 400,
    color: "#262627",
  },

  sortIcon: {
    fontSize: 14,
    lineHeight: "14px",
    color: "#262627",
  },
  sortMenu: {
    position: "absolute",
    right: 0,
    top: 34,
    width: 62,
    height: 124,
    backgroundColor: "#FDFDFD",
    border: "1px solid #E8EBED",
    borderRadius: 12,
    boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
    zIndex: 10,
    paddingTop: 8,
    paddingBottom: 8,
    display: "flex",
    flexDirection: "column",
    gap: 4,
    boxSizing: "border-box",
  },

  sortItem: {
    border: "none",
    background: "transparent",
    cursor: "pointer",
    padding: 0,
    height: 24,
    fontSize: 16, // Body1
    lineHeight: "24px",
    fontWeight: 400,
    color: "#262627",
    textAlign: "center",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 173px)",
    justifyContent: "space-between",
    gap: 12,
  },
};

const cardStyles = {
  card: {
    width: 173,
    height: 173,
    borderRadius: 12,
    overflow: "hidden",
    position: "relative",
    backgroundColor: "#E8EBED",
  },
  imageArea: {
    width: "100%",
    height: "100%",
    position: "relative",
  },
  imagePlaceholder: {
    width: "100%",
    height: "100%",
    backgroundColor: "#C9CDD2",
  },
  image: {
  width: "100%",
  height: "100%",
  objectFit: "cover",
},
  tagBadge: {
    position: "absolute",
    top: 8,
    left: 8,
    height: 20,
    borderRadius: 4,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 11,
    lineHeight: "14px",
    fontWeight: 600,
    color: "#FDFDFD",
  },
  heartButton: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 24,
    height: 24,
    border: "none",
    background: "transparent",
    padding: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
  },
  price: {
    position: "absolute",
    left: 8,
    bottom: 8,
    fontSize: 16,
    lineHeight: "24px",
    fontWeight: 700,
    color: "#FDFDFD",
    textShadow: "0 1px 2px rgba(0,0,0,0.18)",
  },
};
