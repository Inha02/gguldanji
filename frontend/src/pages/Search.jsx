import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { COLORS } from "../constants/colors";

const recentSearches = ["아이폰", "갤럭시북", "에어팟", "트롤리", "장스탠드"];

export default function Search() {
    const navigate = useNavigate();
    const [keyword, setKeyword] = useState("");

    const handleSearch = () => {
        const trimmed = keyword.trim();
        if (!trimmed) return;
        navigate(`/search-result?q=${encodeURIComponent(trimmed)}`);
    };

    return (
        <div style={styles.page}>
            <div style={styles.header}>
                <button
                    type="button"
                    aria-label="뒤로가기"
                    style={styles.backBtn}
                    onClick={() => navigate("/")}
                >
                    <span style={styles.backIcon} />
                </button>

                <input
                    className="search-input"
                    type="text"
                    placeholder="검색어를 입력하세요."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") handleSearch();
                    }}
                    style={styles.searchInput}
                />

                <button
                    type="button"
                    aria-label="검색"
                    style={styles.searchBtn}
                    onClick={handleSearch}
                >
                    <SearchIcon />
                </button>
            </div>

            <div style={styles.main}>
                <div style={styles.sectionTitle}>최근 검색</div>

                <div style={styles.recentList}>
                    {recentSearches.map((item, index) => (
                        <button
                            key={index}
                            type="button"
                            style={styles.recentItem}
                            onClick={() => navigate(`/search-result?q=${encodeURIComponent(item)}`)}
                        >
                            <ClockIcon />
                            <span style={styles.recentText}>{item}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

function SearchIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="6" stroke={COLORS.black} strokeWidth="1.8" />
            <path d="M16 16L20 20" stroke={COLORS.black} strokeWidth="1.8" strokeLinecap="round" />
        </svg>
    );
}

function ClockIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="8" stroke={COLORS.black} strokeWidth="1.8" />
            <path
                d="M12 8v4.5l3 1.8"
                stroke={COLORS.black}
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: COLORS.white,
    },
    header: {
        width: "100%",
        height: 50,
        padding: "13px 16px 0 16px",
        boxSizing: "border-box",
        display: "flex",
        alignItems: "flex-start",
    },
    backBtn: {
        width: 24,
        height: 24,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
        flexShrink: 0,
    },
    backIcon: {
        width: 10,
        height: 10,
        display: "block",
        borderLeft: `2px solid ${COLORS.black}`,
        borderBottom: `2px solid ${COLORS.black}`,
        transform: "rotate(45deg)",
    },
    searchInput: {
        width: 300,
        height: 30,
        marginLeft: 5,
        borderRadius: 30,
        border: `1px solid ${COLORS.gray100}`,
        backgroundColor: COLORS.white,
        padding: "0 12px",
        boxSizing: "border-box",
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: COLORS.black,
        outline: "none",
    },
    searchBtn: {
        width: 24,
        height: 24,
        marginLeft: 5,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
        flexShrink: 0,
    },
    main: {
        padding: "16px 16px 0 16px",
        boxSizing: "border-box",
    },
    sectionTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: COLORS.black,
    },
    recentList: {
        marginTop: 10,
        display: "flex",
        flexDirection: "column",
    },
    recentItem: {
        width: 358,
        height: 40,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "flex",
        alignItems: "center",
        cursor: "pointer",
    },
    recentText: {
        marginLeft: 6,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
    },
};