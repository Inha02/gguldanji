function formatLocation(location) {
    if (!location) return "용산구 청파동";

    const raw = typeof location === "object"
        ? location.address || ""
        : String(location);

    const parts = raw.split(" ").filter(Boolean);

    const guIndex = parts.findIndex((part) => part.endsWith("구"));
    const dongIndex = parts.findIndex(
        (part) =>
            part.endsWith("동") ||
            part.endsWith("읍") ||
            part.endsWith("면")
    );

    if (guIndex !== -1 && dongIndex !== -1 && dongIndex > guIndex) {
        return `${parts[guIndex]} ${parts[dongIndex]}`;
    }

    if (dongIndex !== -1) {
        return parts[dongIndex];
    }

    return "용산구 청파동";
}

export default function ProductCard({
    item,
    showHeart = false,
    liked = false,
    onToggleLike,
}) {
    const locationText = formatLocation(item.location);

    return (
        <div style={styles.card}>
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

                <div style={styles.price}>{item.price}원</div>

                <div style={styles.meta}>
                    {locationText} · {item.time}
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
        width: 173,
        height: 222,
        borderRadius: 12,
        overflow: "hidden",
        background: "#FDFDFD",
        color: "#262627",
        boxSizing: "border-box",
    },

    imageWrap: {
        position: "relative",
        width: 173,
        height: 152,
        flexShrink: 0,
    },

    image: {
        width: 173,
        height: 152,
        background: "#FDFDFD",
    },

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
        height: 70,
        padding: "6px 8px 10px 8px",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
    },

    title: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#1B1D1F",
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
        marginBottom: "2px",
    },

    price: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 700,
        color: "#1B1D1F",
    },

    meta: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#72787F",
        marginTop: "4px",
    },
};