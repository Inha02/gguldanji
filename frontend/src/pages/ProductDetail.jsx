import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { COLORS } from "../constants/colors";

export default function ProductDetail() {
    const navigate = useNavigate();
    const location = useLocation();

    const rawItem = location.state?.item;

    const item = {
        id: rawItem?.id ?? 1,
        title: rawItem?.title ?? "iPhone 14 Pro 256GB",
        price: rawItem?.price ?? "850,000",
        category: rawItem?.category ?? "디지털기기",
        time: rawItem?.time ?? "2시간 전",
        description:
            rawItem?.description ??
            "생활기스 거의 없고 전체적으로 상태 좋습니다. 배터리 효율 양호하고 구성품은 사진 참고 부탁드려요.",
        seller: {
            nickname: rawItem?.seller?.nickname ?? "서초구 불주먹",
            town: rawItem?.seller?.town ?? rawItem?.location ?? "서울 서초구 방배1동  · 서울 용산구 청파동 ",
        },
        images: rawItem?.images ?? [1, 2, 3],
        liked: rawItem?.liked ?? true,
        guideMin: rawItem?.guideMin ?? 600000,
        guideMax: rawItem?.guideMax ?? 850000,
    };

    const [liked, setLiked] = useState(!!item.liked);
    const [currentIndex, setCurrentIndex] = useState(0);

    const images = useMemo(() => item.images || [1], [item.images]);

    const numericPrice = Number(String(item.price).replace(/,/g, ""));

    let guideType = "mid";
    if (numericPrice < item.guideMin) guideType = "low";
    if (numericPrice > item.guideMax) guideType = "high";

    const guideTextMap = {
        low: {
            label: "저가 범위",
            color: "#93C572",
        },
        mid: {
            label: "적정 범위",
            color: "#2699E9",
        },
        high: {
            label: "고가 범위",
            color: "#FF584D",
        },
    };

    const guideInfo = guideTextMap[guideType];

    // 회색 바 기준 경계 위치
    const lowWidth = 28;
    const midLeft = 36;
    const midWidth = 28;

    // 경계값 텍스트 위치 (%)
    const minBoundaryLeft = midLeft;                 // 저가 ↔ 적정 경계
    const maxBoundaryLeft = midLeft + midWidth;      // 적정 ↔ 고가 경계

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <button
                    type="button"
                    aria-label="뒤로가기"
                    style={styles.backBtn}
                    onClick={() => navigate(-1)}
                >
                    <span style={styles.backIcon} />
                </button>

                <div style={styles.headerRight}>
                    <button
                        type="button"
                        aria-label="찜"
                        style={styles.iconBtn}
                        onClick={() => setLiked((prev) => !prev)}
                    >
                        <HeartIcon liked={liked} />
                    </button>

                    <button type="button" aria-label="메뉴" style={styles.iconBtn}>
                        <span style={styles.kebabDots} />
                    </button>
                </div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                {/* 상품 이미지 */}
                <div style={styles.imageSection}>
                    <div style={styles.mainImage}>
                        <button
                            type="button"
                            aria-label="이전 사진"
                            style={styles.imageNavLeft}
                            onClick={() =>
                                setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1))
                            }
                        >
                            ‹
                        </button>

                        <div style={styles.imagePlaceholder}>
                            상품 사진 {currentIndex + 1}
                        </div>

                        <button
                            type="button"
                            aria-label="다음 사진"
                            style={styles.imageNavRight}
                            onClick={() =>
                                setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1))
                            }
                        >
                            ›
                        </button>

                        <div style={styles.dotRow}>
                            {images.map((_, idx) => (
                                <span
                                    key={idx}
                                    style={{
                                        ...styles.dot,
                                        ...(currentIndex === idx ? styles.dotActive : styles.dotInactive),
                                    }}
                                />
                            ))}
                        </div>
                    </div>
                </div>

                {/* 판매자 프로필 */}
                <div style={styles.sellerCard}>
                    <div style={styles.sellerAvatar}>
                        <div style={styles.sellerBear} />
                    </div>

                    <div style={styles.sellerInfo}>
                        <div style={styles.sellerName}>{item.seller.nickname}</div>
                        <div style={styles.sellerTown}>{item.seller.town}</div>
                    </div>
                </div>

                <div style={styles.divider} />

                {/* 상품 정보 */}
                <div style={styles.infoSection}>
                    <div style={styles.itemTitle}>{item.title}</div>
                    <div style={styles.itemPrice}>{item.price}원</div>
                    <div style={styles.itemMeta}>
                        {item.category} · {item.time}
                    </div>
                </div>

                {/* 가격 가이드 */}
                <div style={styles.guideBox}>
                    <div style={styles.guideCaption}>곰곰이의 가격 가이드</div>

                    <div style={styles.guideTextRow}>
                        <div style={styles.guideMainText}>
                            이 가격은{" "}
                            <span style={{ color: guideInfo.color }}>
                                {guideInfo.label}
                            </span>
                            {" "}안에 있어요
                        </div>

                        <div style={styles.guideSubText}>· 유사 상품 5건 기준</div>
                    </div>

                    <div style={styles.guideBarWrap}>
                        <div style={styles.guideBarBg}>
                            <div
                                style={{
                                    ...styles.guideBarActive,
                                    ...(guideType === "low" ? styles.guideBarLow : {}),
                                    ...(guideType === "mid" ? styles.guideBarMid : {}),
                                    ...(guideType === "high" ? styles.guideBarHigh : {}),
                                    backgroundColor: guideInfo.color,
                                }}
                            />
                        </div>

                        {/* 경계 가격 */}
                        <span
                            style={{
                                ...styles.boundaryPriceText,
                                left: `${minBoundaryLeft}%`,
                                transform: "translateX(-50%)",
                            }}
                        >
                            {item.guideMin.toLocaleString()}원
                        </span>

                        <span
                            style={{
                                ...styles.boundaryPriceText,
                                left: `${maxBoundaryLeft}%`,
                                transform: "translateX(-50%)",
                            }}
                        >
                            {item.guideMax.toLocaleString()}원
                        </span>
                    </div>
                </div>
                
                <div style={{height: 18}} />
                <div style={styles.divider} />

                {/* 상품 설명 */}
                <div style={styles.sectionBlock}>
                    <div style={styles.sectionBlockTitle}>상품 설명</div>
                    <div style={styles.sectionBlockBody}>{item.description}</div>
                </div>

                <div style={{ height: 18 }} />
                <div style={styles.divider} />

                {/* 거래 희망 장소 */}
                <div style={styles.sectionBlock}>
                    <div style={styles.sectionBlockTitle}>거래 희망 장소</div>
                    <div style={styles.locationTownText}>{item.seller.town}</div>

                    <div style={styles.mapBox}>
                        <div style={styles.mapPlaceholder}>지도</div>
                    </div>
                </div>

                <div style={{ height: 140 }} />
            </div>

            {/* Bottom Action */}
            <div style={styles.bottomFrame}>
                <button type="button" style={styles.sellerBtn}>
                    판매자 성향
                </button>

                <button type="button" style={styles.chatBtn}>
                    채팅하기
                </button>
            </div>
        </div>
    );
}

function HeartIcon({ liked }) {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M12 21s-6.716-4.35-9.193-8.102C.93 10.066 1.38 6.3 4.404 4.78c2.066-1.038 4.466-.46 5.855 1.205L12 7.89l1.741-1.905c1.39-1.665 3.79-2.243 5.855-1.205 3.024 1.52 3.474 5.286 1.597 8.118C18.716 16.65 12 21 12 21z"
                fill={liked ? "#FF2D55" : "none"}
                stroke={liked ? "#FF2D55" : COLORS.black}
                strokeWidth="1.8"
            />
        </svg>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: COLORS.white,
        display: "flex",
        flexDirection: "column",
        position: "relative",
    },

    header: {
        width: "100%",
        height: 50,
        padding: "13px 16px 0 16px",
        backgroundColor: COLORS.white,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        position: "relative",
        flexShrink: 0,
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
    },

    backIcon: {
        width: 10,
        height: 10,
        display: "block",
        borderLeft: `2px solid ${COLORS.black}`,
        borderBottom: `2px solid ${COLORS.black}`,
        transform: "rotate(45deg)",
    },

    headerRight: {
        display: "flex",
        alignItems: "center",
        gap: 8,
    },

    iconBtn: {
        width: 24,
        height: 24,
        border: "none",
        background: "transparent",
        padding: 0,
        display: "grid",
        placeItems: "center",
        cursor: "pointer",
    },

    kebabDots: {
        width: 3,
        height: 3,
        borderRadius: "50%",
        backgroundColor: COLORS.black,
        boxShadow: `0 -6px 0 ${COLORS.black}, 0 6px 0 ${COLORS.black}`,
    },

    main: {
        flex: 1,
        overflowY: "auto",
        padding: "0 16px 0 16px",
        boxSizing: "border-box",
    },

    imageSection: {
        marginLeft: -16,
        marginRight: -16,
    },

    mainImage: {
        width: "100%",
        height: 390,
        borderTopLeftRadius: 0,
        borderTopRightRadius: 0,
        borderBottomLeftRadius: 20,
        borderBottomRightRadius: 20,
        overflow: "hidden",
        backgroundColor: COLORS.gray100,
        position: "relative",
    },

    imagePlaceholder: {
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: COLORS.gray500,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
    },

    imageNavLeft: {
        position: "absolute",
        left: 12,
        top: "50%",
        transform: "translateY(-50%)",
        width: 36,
        height: 36,
        borderRadius: "50%",
        border: "none",
        background: "rgba(0,0,0,0.35)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        backdropFilter: "blur(4px)",
    },

    imageNavRight: {
        position: "absolute",
        right: 12,
        top: "50%",
        transform: "translateY(-50%)",
        width: 36,
        height: 36,
        borderRadius: "50%",
        border: "none",
        background: "rgba(0,0,0,0.35)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        backdropFilter: "blur(4px)",
    },

    dotRow: {
        position: "absolute",
        left: "50%",
        bottom: 12,
        transform: "translateX(-50%)",
        display: "flex",
        alignItems: "center",
        gap: 6,
    },

    dot: {
        width: 6,
        height: 6,
        borderRadius: "50%",
    },

    dotActive: {
        backgroundColor: COLORS.white,
        opacity: 1,
    },

    dotInactive: {
        backgroundColor: COLORS.white,
        opacity: 0.7,
    },

    sellerCard: {
        marginTop: 18,
        display: "flex",
        alignItems: "center",
        gap: 12,
    },

    sellerAvatar: {
        width: 44,
        height: 44,
        borderRadius: "50%",
        backgroundColor: "rgba(251, 226, 0, 0.3)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
    },

    sellerBear: {
        width: 26,
        height: 26,
        borderRadius: "50%",
        backgroundColor: COLORS.gray100,
    },

    sellerInfo: {
        display: "flex",
        flexDirection: "column",
        gap: 2,
    },

    sellerName: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: COLORS.black,
    },

    sellerTown: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: COLORS.gray500,
    },

    divider: {
        width: "100%",
        height: 1,
        backgroundColor: COLORS.gray100,
        marginTop: 18,
    },

    infoSection: {
        marginTop: 18,
    },

    itemTitle: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
    },

    itemPrice: {
        marginTop: 4,
        fontSize: 24,
        lineHeight: "32px",
        fontWeight: 700,
        color: COLORS.black,
    },

    itemMeta: {
        marginTop: 4,
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: COLORS.gray500,
    },

    guideBox: {
        width: "100%",
        height: 108,
        marginTop: 12,
        borderRadius: 12,
        backgroundColor: "#F7F8F9",
        padding: "10px 12px",
        boxSizing: "border-box",
    },

    guideCaption: {
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: COLORS.black,
    },

    guideTextRow: {
        marginTop: 4,
        display: "flex",
        alignItems: "center",
        gap: 6,
        flexWrap: "wrap",
    },

    guideMainText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: COLORS.black,
    },

    guideSubText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: COLORS.black,
    },

    guideBarWrap: {
        marginTop: 8,
        position: "relative",
        paddingBottom: 18,
    },

    guideBarBg: {
        width: 334,
        height: 18,
        borderRadius: 12,
        backgroundColor: COLORS.gray100,
        position: "relative",
        overflow: "hidden",
    },

    guideBarActive: {
        position: "absolute",
        top: 0,
        height: "100%",
        borderRadius: 12,
    },

    guideBarLow: {
        left: 0,
        width: "28%",
    },

    guideBarMid: {
        left: "36%",
        width: "28%",
    },

    guideBarHigh: {
        right: 0,
        width: "28%",
    },

    boundaryPriceText: {
        position: "absolute",
        top: 22,
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: COLORS.gray500,
        whiteSpace: "nowrap",
    },
    sectionBlock: {
        marginTop: 18,
    },

    sectionBlockTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: COLORS.black,
    },

    sectionBlockBody: {
        marginTop: 4,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
        whiteSpace: "pre-line",
    },

    locationTownText: {
        marginTop: 4,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
    },

    mapBox: {
        width: 358,
        height: 128,
        marginTop: 8,
        borderRadius: 12,
        overflow: "hidden",
        backgroundColor: COLORS.gray100,
    },

    mapPlaceholder: {
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: COLORS.gray500,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
    },

    bottomFrame: {
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        height: 56,
        backgroundColor: COLORS.white,
        padding: "0 16px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        boxSizing: "border-box",
    },

    sellerBtn: {
        width: 173,
        height: 42,
        borderRadius: 16,
        border: "none",
        backgroundColor: COLORS.gray100,
        color: COLORS.black,
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    chatBtn: {
        width: 173,
        height: 42,
        borderRadius: 16,
        border: "none",
        backgroundColor: COLORS.primary,
        color: COLORS.black,
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },
};