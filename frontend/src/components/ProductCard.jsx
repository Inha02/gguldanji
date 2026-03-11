export default function ProductCard({
    item,
    showHeart = false,     // Likes에서만 true로 줄거임
    liked = false,         // Likes에서만 관리
    onToggleLike,          // Likes에서만 전달
}) {
    return (
        <div style={styles.card}>
            {/* 이미지 영역: 하트가 카드 위에 올라가야 하니까 relative */}
            <div style={styles.imageWrap}>
                <div style={styles.image} />

                {showHeart && (
                    <button
                        type="button"
                        aria-label="찜 토글"
                        onClick={onToggleLike}
                        style={styles.heartBtn}
                    >
                        <HeartIcon filled={liked} />
                    </button>
                )}
            </div>

            <div style={styles.body}>
                <div style={styles.title}>{item.title}</div>

                {/* price + tag(저가/상가/적정) 같이 쓰는 버전이면 여기에 붙이면 됨 */}
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <div style={styles.price}>{item.price}원</div>
                    {item.tag && (
                        <span
                            style={{
                                ...styles.tag,
                                background:
                                    item.tag === "저가"
                                        ? "#93C572"
                                        : item.tag === "상가"
                                            ? "#FF6666"
                                            : "#2699E9",
                            }}
                        >
                            {item.tag}
                        </span>
                    )}
                </div>

                <div style={styles.meta}>
                    {item.location} · {item.time}
                </div>
            </div>
        </div>
    );
}

function HeartIcon({ filled }) {
    const fill = filled ? "#FF2D55" : "#C9CDD2";
    const stroke = filled ? "#FF2D55" : "#C9CDD2";


    return (
        <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
           2 6 4 4 6.5 4
           8.24 4 9.91 4.81 11 6.09
           12.09 4.81 13.76 4 15.5 4
           18 4 20 6 20 8.5
           20 12.28 16.6 15.36 13.45 20.03
           L12 21.35z"
                fill={fill}
                stroke={stroke}
                strokeWidth="1.8"
                strokeLinejoin="round"
            />
        </svg>
    );
}


const styles = {
    card: {
        borderRadius: 12,
        overflow: "hidden",
        background: "#FDFDFD",
        color: "#262627",
    },

    // 하트 올릴 수 있게 감싸기
    imageWrap: {
        position: "relative",
    },

    image: {
        height: 152, // 네가 말한 카드 이미지 영역
        background: "#FDFDFD",
    },

    // 하트 위치: top 11.5 / right 8
    heartBtn: {
        position: "absolute",
        top: 11.5,
        right: 8,
        width: 28,
        height: 28,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    body: {
        padding: 8,
        display: "flex",
        flexDirection: "column",
    },

    // Body2 (14/20)
    title: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        marginTop: 6,      // image-제목 간격 6
        marginBottom: 2,   // 제목-가격 간격 2
        color: "#1B1D1F",
        display: "-webkit-box",
        WebkitLineClamp: 2,
        WebkitBoxOrient: "vertical",
        overflow: "hidden",
    },

    // Small Text Bold (11/14)
    price: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 700,
        color: "#1B1D1F",
        marginBottom: 4,   // 가격-메타 간격(타이틀 기준으로 맞추려면 여기 4)
    },

    // tag 22x14 hug 느낌
    tag: {
        height: 14,
        padding: "0 6px",
        borderRadius: 4,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 10,
        lineHeight: "14px",
        fontWeight: 700,
        color: "#FDFDFD",
    },

    // Small Text (11/14)
    meta: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#72787F",
    },
};
