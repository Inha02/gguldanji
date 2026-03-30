import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { COLORS } from "../constants/colors";
import { getPriceEstimate } from "../api/ai";
import { useChat } from "../context/ChatContext";


function getImageUrl(path) {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return `http://localhost:4000/${path}`;
}

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

export default function ProductDetail() {
    
    const { addRoom } = useChat();
    const navigate = useNavigate();
    const location = useLocation();

    const rawItem = location.state?.item;
    console.log("rawItem:", rawItem);

    const categoryId = rawItem?.categoryId ?? rawItem?.category?._id ?? "";

    const categoryName =
    CATEGORY_MAP[categoryId] ||
    rawItem?.category?.name ||
    rawItem?.category ||
    "디지털기기";

    const item = {
        id: rawItem?.id ?? 1,
        _id: rawItem?._id ?? rawItem?.id ?? 1,
        title: rawItem?.title ?? "iPhone 14 Pro 256GB",
        price: rawItem?.price ?? "850,000",
        category: categoryName,
        categoryId: categoryId,
        condition: rawItem?.condition ?? "A급",
        sellerId:
            rawItem?.sellerId ??
            rawItem?.seller?._id ??
            rawItem?.seller?.id ??
            "",
        time: rawItem?.time ?? "2시간 전",
        description:
            rawItem?.description ??
            "생활기스 거의 없고 전체적으로 상태 좋습니다. 배터리 효율 양호하고 구성품은 사진 참고 부탁드려요.",
        seller: {
            sellerId:
                rawItem?.sellerId ??
                rawItem?.seller?._id ??
                rawItem?.seller?.id ??
                "",
            nickname: rawItem?.seller?.nickname ?? "서초구 불주먹",
            town:
                rawItem?.seller?.town ??
                rawItem?.location ??
                "서울 서초구 방배1동 · 서울 용산구 청파동",
        },
        images: Array.isArray(rawItem?.images) ? rawItem.images : [],
        liked: rawItem?.liked ?? true,
        guideMin: rawItem?.guideMin ?? 600000,
        guideMax: rawItem?.guideMax ?? 850000,
        sellerAnalysis: rawItem?.sellerAnalysis ?? null,
    };

    console.log("item:", item);

    const [liked, setLiked] = useState(!!item.liked);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isSellerSheetOpen, setIsSellerSheetOpen] = useState(false);
    const [priceGuide, setPriceGuide] = useState(null);

    const [sellerAnalysis, setSellerAnalysis] = useState(item.sellerAnalysis ?? null);
    const [isSellerLoading, setIsSellerLoading] = useState(false);
    const [chatLogs, setChatLogs] = useState(null);

    const [menuOpen, setMenuOpen] = useState(false);

    const [sellerInfo, setSellerInfo] = useState({
        nickname: item.seller.nickname,
        town: item.seller.town,
        profileImage: "",
        trustScore: null,
      });

    useEffect(() => {
        const fetchPriceGuide = async () => {
            if (!item.categoryId) {
                console.warn("categoryId가 없어서 AI 가격 가이드를 호출하지 않습니다.");
                return;
            }

            console.log("detail item.category:", item.category);
            console.log("detail item.categoryId:", item.categoryId);

            try {
                const payload = {
                    title: item.title || "",
                    description: item.description || "",
                    category: item.category || "",
                    categoryId: item.categoryId || "",
                    condition: item.condition || "A급",
                    price: Number(String(item.price).replace(/,/g, "")) || 0,
                    images: Array.isArray(item.images) ? item.images : [],
                };

                console.log("AI price payload:", JSON.stringify(payload,null,2));

                const result = await getPriceEstimate(payload);
                console.log("AI 가격 가이드 응답:", result);

                setPriceGuide(result);
            } catch (error) {
                console.error("AI 가격 가이드 호출 실패:", error);
                console.error("에러 응답 데이터:", error.response?.data);
                console.error("에러 details:",JSON.stringify(error.response?.data?.details,null,2));
            }
        };

        fetchPriceGuide();
    }, [item.categoryId, item.title, item.description, item.price, item.images]);

    useEffect(() => {
        const fetchSellerInfo = async () => {
          if (!item.sellerId) {
            console.warn("sellerId가 없어서 판매자 정보를 조회하지 않습니다.");
            return;
          }
      
          try {
            const token = localStorage.getItem("token");
      
            const res = await fetch(`http://localhost:4000/users/${item.sellerId}`, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
      
            if (!res.ok) {
              throw new Error(`판매자 정보 조회 실패: ${res.status}`);
            }
      
            const data = await res.json();
            console.log("판매자 정보 응답:", data);
      
            setSellerInfo({
              nickname: data.nickname ?? item.seller.nickname,
              town: item.seller.town, // user 응답에 town이 없으면 기존 location 유지
              profileImage: data.profileImage ?? "",
              trustScore: data.trustScore ?? null,
            });
          } catch (err) {
            console.error("판매자 정보 조회 실패:", err);
          }
        };
      
        fetchSellerInfo();
      }, [item.sellerId]);

    const images = useMemo(() => item.images || [], [item.images]);

    const numericPrice = Number(String(item.price).replace(/,/g, ""));
    
    const guideMin = Number(
        priceGuide?.buyer_range?.min ??
        item.guideMin
    );
    
    const guideMax = Number(
        priceGuide?.buyer_range?.max ??
        item.guideMax
    );
    
    const barMin = Number(
        priceGuide?.price_range_min ??
        guideMin
    );
    
    const barMax = Number(
        priceGuide?.price_range_max ??
        guideMax
    );
    
    const ragCount = priceGuide?.rag_sample_count ?? 5;

    let guideType = "mid";
    if (numericPrice < guideMin) guideType = "low";
    if (numericPrice > guideMax) guideType = "high";

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

    const totalRange = barMax - barMin;
    const midLeft = totalRange > 0 ? ((guideMin - barMin) / totalRange) * 100 : 20;
    const midWidth = totalRange > 0 ? ((guideMax - guideMin) / totalRange) * 100 : 60;

    const minBoundaryLeft = midLeft;
    const maxBoundaryLeft = midLeft + midWidth;

    const handleOpenSellerProfile = async () => {
        try {
          setIsSellerLoading(true);
      
          const token = localStorage.getItem("token");
      
          const res = await fetch("http://localhost:4000/ai/seller-profile", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              seller_id: item.sellerId,
              chat_logs: [ // 여기는 실제 채팅 로그 데이터로 교체해야 함
                {"role": "buyer", "message": "안녕하세요, 아직 판매중인가요?", "timestamp": "2026-03-01T10:00:00"},
                {"role": "seller", "message": "네 판매중입니다", "timestamp": "2026-03-01T10:01:00"},
                {"role": "buyer", "message": "상태 어떤가요?", "timestamp": "2026-03-01T10:02:00"},
                {"role": "seller", "message": "사용감 거의 없고요, 기스 없습니다. 구매한지 3개월 됐어요. 박스랑 충전기 다 있습니다.", "timestamp": "2026-03-01T10:03:00"},
                {"role": "buyer", "message": "15만원에 가능할까요?", "timestamp": "2026-03-01T10:05:00"},
                {"role": "seller", "message": "18만원까지는 가능합니다. 그 이하는 어렵습니다.", "timestamp": "2026-03-01T10:06:00"},
                {"role": "buyer", "message": "알겠습니다. 직거래 가능한가요?", "timestamp": "2026-03-01T10:07:00"},
                {"role": "seller", "message": "강남역 가능합니다. 오늘 저녁 7시 어떠세요?", "timestamp": "2026-03-01T10:08:00"},
                {"role": "buyer", "message": "네 좋습니다!", "timestamp": "2026-03-01T10:09:00"},
                {"role": "seller", "message": "오늘 7시 강남역 11번출구에서 뵙겠습니다.", "timestamp": "2026-03-01T10:10:00"}
              ],
              existing_profile: null,
              all_chat_logs: null,
            }),
          });
      
          const contentType = res.headers.get("content-type") || "";

          if (!contentType.includes("application/json")) {
            const text = await res.text();
            console.error("JSON 아닌 응답:", text);
            throw new Error("서버가 JSON이 아닌 응답을 반환했습니다.");
          }

        const data = await res.json();
          console.log("판매자 성향 분석 응답:", data);
      
          const mapped = mapSellerProfileToUI(data);
          console.log("sellerAnalysis:", mapped);

          setSellerAnalysis(mapped);
          setIsSellerSheetOpen(true);
        } catch (err) {
          console.error("판매자 성향 분석 실패:", err);
          setIsSellerSheetOpen(true);
        } finally {
          setIsSellerLoading(false);
        }
      };


      useEffect(() => {
  const checkLiked = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await fetch(
        `http://localhost:4000/likes/me/${item._id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await res.json();

      setLiked(data.liked);
    } catch (err) {
      console.error("좋아요 상태 조회 실패:", err);
    }
  };

  if (item._id) checkLiked();
}, [item._id]);

const handleLike = async () => {
  try {
    const token = localStorage.getItem("token");

    const res = await fetch("http://localhost:4000/likes/toggle", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        postId: item._id,
      }),
    });

    const data = await res.json();

    // 🔥 서버 기준으로 상태 반영
    setLiked(data.liked);

  } catch (err) {
    console.error("좋아요 실패:", err);
  }
};
    return (
        <div style={styles.page}>
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
                        onClick={handleLike}
                    >
                        <HeartIcon liked={liked} />
                    </button>

                    
                    <div style={styles.kebabWrap}>
                        <button
                            type="button"
                            aria-label="메뉴"
                            style={styles.iconBtn}
                            onClick={() => setMenuOpen((prev) => !prev)}
                        >
                            <span style={styles.kebabDots} />
                        </button>

                        {menuOpen && (
                            <div style={styles.kebabMenu}>
                                <button
                                    type="button"
                                    style={styles.kebabMenuItem}
                                    onClick={() => {
                                        setMenuOpen(false);
                                        console.log("신고하기 클릭");
                                    }}
                                >
                                    신고하기
                                </button>

                                <button
                                    type="button"
                                    style={styles.kebabMenuItem}
                                    onClick={() => {
                                        setMenuOpen(false);
                                        console.log("차단하기 클릭");
                                    }}
                                >
                                    차단하기
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div style={styles.main}>
                <div style={styles.imageSection}>
                    <div style={styles.mainImage}>
                        <button
                            type="button"
                            aria-label="이전 사진"
                            style={styles.imageNavLeft}
                            onClick={() =>
                                setCurrentIndex((prev) =>
                                    prev === 0 ? images.length - 1 : prev - 1
                                )
                            }
                        >
                            <ArrowLeft />
                        </button>

                        {images.length > 0 ? (
                            <img
                                src={getImageUrl(images[currentIndex])}
                                alt={item.title}
                                style={styles.detailImage}
                            />
                        ) : (
                            <div style={styles.imagePlaceholder}>
                                상품 사진 {currentIndex + 1}
                            </div>
                        )}

                        <button
                            type="button"
                            aria-label="다음 사진"
                            style={styles.imageNavRight}
                            onClick={() =>
                                setCurrentIndex((prev) =>
                                    prev === images.length - 1 ? 0 : prev + 1
                                )
                            }
                        >
                            <ArrowRight />
                        </button>

                        <div style={styles.dotRow}>
                            {images.map((_, idx) => (
                                <span
                                    key={idx}
                                    style={{
                                        ...styles.dot,
                                        ...(currentIndex === idx
                                            ? styles.dotActive
                                            : styles.dotInactive),
                                    }}
                                />
                            ))}
                        </div>
                    </div>
                </div>

                <div style={styles.sellerCard}>
                    <div style={styles.sellerAvatar}>
                        {sellerInfo.profileImage ? (
                            <img
                            src={sellerInfo.profileImage}
                            alt={sellerInfo.nickname}
                            style={styles.sellerAvatarImage}
                            />
                        ) : (
                            <div style={styles.sellerBear} />
                        )}
                    </div>

                    <div style={styles.sellerInfo}>
                        <div style={styles.sellerName}>{sellerInfo.nickname}</div>
                        <div style={styles.sellerTown}>{sellerInfo.town}</div>
                    </div>
                </div>

                <div style={styles.divider} />

                <div style={styles.infoSection}>
                    <div style={styles.itemTitle}>{item.title}</div>
                    <div style={styles.itemPrice}>
                        {item.price}원
                    </div>
                    <div style={styles.itemMeta}>
                        {item.category} · {item.time}
                    </div>
                </div>

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

                        <div style={styles.guideSubText}>· 유사 상품 {ragCount}건 기준</div>
                    </div>

                    <div style={styles.guideBarWrap}>
                        <div style={styles.guideBarBg}>
                            <div
                                style={{
                                    ...styles.guideBarActive,
                                    ...(guideType === "low"
                                        ? { left: 0, width: `${midLeft}%` }
                                        : guideType === "mid"
                                            ? { left: `${midLeft}%`, width: `${midWidth}%` }
                                            : { left: `${midLeft + midWidth}%`, width: `${100 - midLeft - midWidth}%` }),
                                    backgroundColor: guideInfo.color,
                                }}
                            />
                        </div>

                        <span
                            style={{
                                ...styles.boundaryPriceText,
                                left: `${minBoundaryLeft}%`,
                                transform: "translateX(-50%)",
                            }}
                        >
                            {guideMin.toLocaleString()}원
                        </span>

                        <span
                            style={{
                                ...styles.boundaryPriceText,
                                left: `${maxBoundaryLeft}%`,
                                transform: "translateX(-50%)",
                            }}
                        >
                            {guideMax.toLocaleString()}원
                        </span>
                    </div>
                </div>

                <div style={{ height: 18 }} />
                <div style={styles.divider} />

                <div style={styles.sectionBlock}>
                    <div style={styles.sectionBlockTitle}>상품 설명</div>
                    <div style={styles.sectionBlockBody}>{item.description}</div>
                </div>

                <div style={{ height: 18 }} />
                <div style={styles.divider} />

                <div style={styles.sectionBlock}>
                    <div style={styles.sectionBlockTitle}>거래 희망 장소</div>
                    <div style={styles.locationTownText}>{item.seller.town}</div>

                    {/* <div style={styles.mapBox}>
                        <div style={styles.mapPlaceholder}>지도</div>
                    </div> */}
                </div>

                <div style={{ height: 140 }} />
            </div>

            <div style={styles.bottomFrame}>
                <button
                    type="button"
                    style={styles.sellerBtn}
                    onClick={handleOpenSellerProfile}
                >
                    판매자 성향
                </button>

                <button
                    type="button"
                    style={styles.chatBtn}
                    onClick={async () => {
                        try {
                            const token = localStorage.getItem("token");

                            if (!item.sellerId) {
                                alert("sellerId 없음");
                                console.log("❌ sellerId:", item.sellerId);
                                return;
                            }

                            const res = await fetch("http://localhost:4000/chat/rooms", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    Authorization: `Bearer ${token}`,
                                },
                                body: JSON.stringify({
                                    postId: item._id,
                                    sellerId: item.sellerId,
                                }),
                            });

                            const data = await res.json();

                            addRoom({
  id: data.room._id,
  name: item.seller.nickname,
  messages: [],
  tag: "적정",
});

                            navigate(`/chat/${data.room._id}`, {
                                state: {
                                    seller: item.seller,
                                    product: item.title,
                                    price: item.price,
                                },
                            });
                        } catch (err) {
                            console.error("채팅방 생성 실패:", err);
                        }
                    }}
                >
                    채팅하기
                </button>
            </div>

            {isSellerSheetOpen && (
                <div
                    style={styles.sheetBackdrop}
                    onClick={() => setIsSellerSheetOpen(false)}
                >
                    <div
                        style={{
                            ...styles.sellerSheet,
                            height: sellerAnalysis ? 496 : 138,
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={styles.sheetHandle} />

                        <div style={styles.sheetTitle}>판매자 성향 분석</div>

                        {sellerAnalysis ? (
                            <>
                                <div style={styles.sheetSummaryBox}>
                                    {sellerAnalysis .summary}
                                </div>

                                <div style={styles.sheetSection}>
                                    <div style={styles.sheetSectionTitleOrange}>거래 동기</div>
                                    <TraitBar
                                        label="가격 민감도"
                                        value={sellerAnalysis.tradeMotivation.priceSensitivity}
                                        color="#FF8D28"
                                    />
                                    <TraitBar
                                        label="효율 지향"
                                        value={sellerAnalysis.tradeMotivation.efficiency}
                                        color="#FF8D28"
                                    />
                                    <TraitBar
                                        label="거래 즐김"
                                        value={sellerAnalysis.tradeMotivation.enjoyment}
                                        color="#FF8D28"
                                    />
                                    <TraitBar
                                        label="협상 유연성"
                                        value={sellerAnalysis.tradeMotivation.flexibility}
                                        color="#FF8D28"
                                    />
                                </div>

                                <div style={styles.sheetSection}>
                                    <div style={styles.sheetSectionTitleBlue}>커뮤니케이션 스타일</div>
                                    <TraitBar
                                        label="응답 패턴"
                                        value={sellerAnalysis.communication.responsePattern}
                                        color="#2699E9"
                                    />
                                    <TraitBar
                                        label="정보 제공"
                                        value={sellerAnalysis.communication.information}
                                        color="#2699E9"
                                    />
                                    <TraitBar
                                        label="친근함"
                                        value={sellerAnalysis.communication.friendliness}
                                        color="#2699E9"
                                    />
                                    <TraitBar
                                        label="설명 명확도"
                                        value={sellerAnalysis.communication.clarity}
                                        color="#2699E9"
                                    />
                                </div>

                                <div style={styles.sheetSection}>
                                    <div style={styles.sheetSectionTitleGreen}>신뢰 구축</div>
                                    <TraitBar
                                        label="제품 설명"
                                        value={sellerAnalysis.trust.productDescription}
                                        color="#93C572"
                                    />
                                    <TraitBar
                                        label="거래 투명성"
                                        value={sellerAnalysis.trust.transparency}
                                        color="#93C572"
                                    />
                                    <TraitBar
                                        label="문제 대응"
                                        value={sellerAnalysis.trust.problemSolving}
                                        color="#93C572"
                                    />
                                </div>
                            </>
                        ) : (
                            <div style={styles.sheetSummaryBox}>
                                아직 분석 데이터가 부족합니다.
                                <br />
                                판매자의 채팅이 쌓이면 자동으로 분석됩니다.
                            </div>
                        )}
                    </div>
                </div>
            )}
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

function ArrowLeft() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M15 18l-6-6 6-6"
                stroke="#FDFDFD"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
            />
        </svg>
    );
}

function ArrowRight() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M9 6l6 6-6 6"
                stroke="#FDFDFD"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
            />
        </svg>
    );
}

function TraitBar({ label, value, color }) {
    const safeValue = Math.max(0, Math.min(Number(value) || 0, 5));
    const percent = (safeValue / 5) * 100;

    return (
        <div style={traitStyles.row}>
            <div style={traitStyles.label}>{label}</div>
            <div style={traitStyles.barWrap}>
                <div style={traitStyles.barBg}>
                    <div
                        style={{
                            ...traitStyles.barFill,
                            width: `${percent}%`,
                            backgroundColor: color,
                            opacity: 0.7,
                        }}
                    />
                    {[1, 2, 3, 4].map((step) => (
                        <span
                            key={step}
                            style={{
                                ...traitStyles.barDivider,
                                left: `${(step / 5) * 100}%`,
                            }}
                        />
                    ))}
                </div>
            </div>
            <div style={traitStyles.value}>{safeValue}/5</div>
        </div>
    );
}

function mapSellerProfileToUI(data) {
    const profile = data?.profile;
    const d = profile?.dimensions;
  
    if (!profile || !d) return null;
  
    return {
      summary: profile.analysis_summary ?? "",
      tradeMotivation: {
        priceSensitivity: d.transaction_motivation?.price_sensitivity?.score ?? 0,
        efficiency: d.transaction_motivation?.efficiency_orientation?.score ?? 0,
        enjoyment: d.transaction_motivation?.enjoyment_orientation?.score ?? 0,
        flexibility: d.transaction_motivation?.negotiation_flexibility?.score ?? 0,
      },
      communication: {
        responsePattern: d.communication_style?.response_pattern?.score ?? 0,
        information: d.communication_style?.information_proactivity?.score ?? 0,
        friendliness: d.communication_style?.tone_friendliness?.score ?? 0,
        clarity: d.communication_style?.clarity_structure?.score ?? 0,
      },
      trust: {
        productDescription: d.trust_building?.product_description_detail?.score ?? 0,
        transparency: d.trust_building?.transaction_transparency?.score ?? 0,
        problemSolving: d.trust_building?.issue_handling_attitude?.score ?? 0,
      },
      rawProfile: profile,
    };
  }


const traitStyles = {
    row: {
        display: "grid",
        gridTemplateColumns: "52px 1fr 24px",
        alignItems: "center",
        columnGap: 8,
        marginTop: 6,
    },

    label: {
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: COLORS.black,
        whiteSpace: "nowrap",
    },

    barWrap: {
        display: "flex",
        alignItems: "center",
    },

    barBg: {
        width: "260px",
        height: 10,
        borderRadius: 12,
        backgroundColor: COLORS.gray100,
        overflow: "hidden",
    },

    barFill: {
        height: "100%",
        borderRadius: 12,
    },

    value: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: COLORS.gray500,
        textAlign: "right",
    },
};

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

    detailImage: {
        width: "100%",
        height: "100%",
        objectFit: "cover",
        display: "block",
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
        padding: 0,
        zIndex: 2,
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
        padding: 0,
        zIndex: 2,
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

    sellerAvatarImage: {
        width: "100%",
        height: "100%",
        objectFit: "cover",
        borderRadius: "50%",
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

    sheetBackdrop: {
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.2)",
        zIndex: 999,
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
    },

    sellerSheet: {
        width: "100%",
        maxWidth: 390,
        backgroundColor: COLORS.white,
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        padding: "12px 16px 20px 16px",
        boxSizing: "border-box",
        overflowY: "auto",
    },

    sheetHandle: {
        width: 100,
        height: 4,
        borderRadius: 4,
        backgroundColor: COLORS.gray200,
        margin: "0 auto 16px auto",
    },

    sheetTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: COLORS.black,
    },

    sheetSummaryBox: {
        marginTop: 16,
        width: "100%",
        minHeight: 52,
        borderRadius: 12,
        backgroundColor: COLORS.gray100,
        padding: "12px 14px",
        boxSizing: "border-box",
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: COLORS.black,
    },

    sheetSection: {
        marginTop: 16,
    },

    sheetSectionTitleOrange: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: "#FF8D28",
    },

    sheetSectionTitleBlue: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: "#2699E9",
    },

    sheetSectionTitleGreen: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 700,
        color: "#93C572",
    },

    kebabWrap: {
        position: "relative",
    },

    kebabMenu: {
        position: "absolute",
        right: 0,
        top: 30,
        width: 88,
        backgroundColor: "#FDFDFD",
        border: `1px solid ${COLORS.gray100}`,
        borderRadius: 12,
        boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
        zIndex: 20,
        padding: "8px 0",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        boxSizing: "border-box",
    },

    kebabMenuItem: {
        width: "100%",
        height: 24,
        border: "none",
        background: "transparent",
        cursor: "pointer",
        padding: 0,
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: COLORS.black,
        textAlign: "center",
    },
};