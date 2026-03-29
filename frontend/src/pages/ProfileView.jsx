import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ProfileAvatar from "../components/ProfileAvatar";

const imagePool = [
    "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/posts/images/가구_인테리어/da6bdb361b3a62cf91315094_0.png",
    "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/posts/images/가구_인테리어/0bd4104bf6c75682b1ae6f4e_0.png",
    "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/posts/images/가구_인테리어/61809e95d0d001fc33d36b0b_0.png",
    "https://gguldanji-images.s3.ap-southeast-2.amazonaws.com/posts/images/가구_인테리어/8c05485ad618049fb3c7781b_0.png",
];

function getStableImage(id) {
    return imagePool[id % imagePool.length];
}


const soldItems = [
  { id: 1 },
  { id: 2 },
  { id: 3 },
  { id: 4 },
];

const reviewTags = ["#친절해요", "#설명이 자세해요", "#네고왕"];

function TraitBarSection({ title, titleColor, data, fillColor }) {
  return (
    <div style={styles.traitSection}>
      <div style={{ ...styles.traitTitle, color: titleColor }}>{title}</div>

      <div style={styles.traitList}>
        {data.map((item) => (
          <div key={item.label} style={styles.traitRow}>
            <div style={styles.traitLabel}>{item.label}</div>

            <div style={styles.traitBarWrap}>
              <div style={styles.traitBarBg}>
                <div
                  style={{
                    ...styles.traitBarFill,
                    width: `${(item.value / 5) * 100}%`,
                    backgroundColor: fillColor,
                  }}
                />
              </div>
            </div>

            <div style={styles.traitValue}>{item.value}/5</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function mapSellerProfileToUI(data) {
  const profile = data?.profile;
  const d = profile?.dimensions;

  if (!profile || !d) return null;

  return {
    summary: profile.analysis_summary ?? "",
    motivationData: [
      { label: "가격 민감도", value: d.transaction_motivation?.price_sensitivity?.score ?? 0 },
      { label: "효율 지향", value: d.transaction_motivation?.efficiency_orientation?.score ?? 0 },
      { label: "거래 즐김", value: d.transaction_motivation?.enjoyment_orientation?.score ?? 0 },
      { label: "협상 유연성", value: d.transaction_motivation?.negotiation_flexibility?.score ?? 0 },
    ],
    communicationData: [
      { label: "응답 패턴", value: d.communication_style?.response_pattern?.score ?? 0 },
      { label: "정보 제공", value: d.communication_style?.information_proactivity?.score ?? 0 },
      { label: "친근함", value: d.communication_style?.tone_friendliness?.score ?? 0 },
      { label: "설명 명확도", value: d.communication_style?.clarity_structure?.score ?? 0 },
    ],
    trustData: [
      { label: "제품 설명", value: d.trust_building?.product_description_detail?.score ?? 0 },
      { label: "거래 투명성", value: d.trust_building?.transaction_transparency?.score ?? 0 },
      { label: "문제 대응", value: d.trust_building?.issue_handling_attitude?.score ?? 0 },
    ],
  };
}

export default function ProfileView() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("거래");

  const [me, setMe] = useState(null);
  const [sellerAnalysis, setSellerAnalysis] = useState(null);
  const [isSellerAnalysisLoading, setIsSellerAnalysisLoading] = useState(false);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const token = localStorage.getItem("token");

        const res = await fetch("http://localhost:4000/users/me", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error(`내 정보 조회 실패: ${res.status}`);
        }

        const data = await res.json();
        console.log("내 정보:", data);
        setMe(data);
      } catch (err) {
        console.error("내 정보 조회 실패:", err);
      }
    };

    fetchMe();
  }, []);

  useEffect(() => {
    const fetchMySellerProfile = async () => {
      if (!me?._id) return;

      try {
        setIsSellerAnalysisLoading(true);

        const token = localStorage.getItem("token");

        const res = await fetch("http://localhost:4000/ai/seller-profile", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            seller_id: me._id,
            chat_logs: [
              { role: "buyer", message: "안녕하세요, 아직 판매중인가요?", timestamp: "2026-03-01T10:00:00" },
              { role: "seller", message: "네 판매중입니다", timestamp: "2026-03-01T10:01:00" },
              { role: "buyer", message: "상태 어떤가요?", timestamp: "2026-03-01T10:02:00" },
              { role: "seller", message: "사용감 거의 없고요, 기스 없습니다.", timestamp: "2026-03-01T10:03:00" },
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

                        <div style={styles.soldList}>
                            {soldItems.map((item) => (
                                <img
                                    key={item.id}
                                    src={getStableImage(item.id)}
                                    alt="최근 거래 상품"
                                    style={styles.soldItem}
                                />
                            ))}
                        </div>

        console.log("내 판매 성향 분석 응답:", data);

        const mapped = mapSellerProfileToUI(data);
        setSellerAnalysis(mapped);
      } catch (err) {
        console.error("내 판매 성향 분석 실패:", err);
      } finally {
        setIsSellerAnalysisLoading(false);
      }
    };

    fetchMySellerProfile();
  }, [me]);

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <button
          type="button"
          aria-label="뒤로가기"
          style={styles.backBtn}
          onClick={() => navigate("/mypage")}
        >
          <span style={styles.backIcon} />
        </button>

        <div style={styles.headerTitle}>나의 프로필</div>

        <div style={styles.headerRight}>
          <button type="button" aria-label="공유" style={styles.iconBtn}>
            <span style={styles.shareIcon}>↥</span>
          </button>

          <button type="button" aria-label="메뉴" style={styles.iconBtn}>
            <span style={styles.kebabDots} />
          </button>
        </div>
      </div>

      <div style={styles.main}>
        <div style={styles.profileTop}>
          <ProfileAvatar size={90} />
          <div style={styles.profileInfo}>
            <div style={styles.name}>{me?.nickname ?? "사용자"}</div>
            <div style={styles.subText}>
              가입일: {me?.createdAt ? new Date(me.createdAt).toLocaleDateString("ko-KR") : "-"}
            </div>
            <div style={styles.subText}>인증한 동네: 청파동, 방배1동</div>
          </div>
        </div>

        <div style={styles.tabRow}>
          <button
            type="button"
            onClick={() => setActiveTab("거래")}
            style={{
              ...styles.tabBtn,
              ...(activeTab === "거래" ? styles.tabBtnActive : {}),
            }}
          >
            거래
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("판매 성향")}
            style={{
              ...styles.tabBtn,
              ...(activeTab === "판매 성향" ? styles.tabBtnActive : {}),
            }}
          >
            판매 성향
          </button>
        </div>

        {activeTab === "거래" && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>최근 거래 요약</div>
            <div style={styles.sectionSubTitle}>최근 판매한 상품 리스트</div>

            <div style={styles.soldList}>
              {soldItems.map((item) => (
                <div key={item.id} style={styles.soldItem} />
              ))}
            </div>

            <div style={styles.keywordTitle}>키워드 태그</div>

            <div style={styles.tagList}>
              {reviewTags.map((tag) => (
                <div key={tag} style={styles.tagItem}>
                  {tag}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "판매 성향" && (
          <div style={styles.section}>
            {isSellerAnalysisLoading ? (
              <div style={styles.summaryBox}>판매 성향을 분석 중입니다.</div>
            ) : sellerAnalysis ? (
              <>
                <div style={styles.summaryBox}>{sellerAnalysis.summary}</div>

                <TraitBarSection
                  title="거래 동기"
                  titleColor="#FF8D28"
                  data={sellerAnalysis.motivationData}
                  fillColor="rgba(255, 141, 40, 0.6)"
                />

                <TraitBarSection
                  title="커뮤니케이션 스타일"
                  titleColor="#2699E9"
                  data={sellerAnalysis.communicationData}
                  fillColor="rgba(38, 153, 233, 0.6)"
                />

                <TraitBarSection
                  title="신뢰 구축"
                  titleColor="#93C572"
                  data={sellerAnalysis.trustData}
                  fillColor="rgba(147, 197, 114, 0.6)"
                />
              </>
            ) : (
              <div style={styles.summaryBox}>아직 분석 데이터가 부족합니다.</div>
            )}
          </div>
        )}
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
        justifyContent: "center",
        position: "relative",
    },

    backBtn: {
        position: "absolute",
        left: 16,
        top: 13,
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
        borderLeft: "2px solid #262627",
        borderBottom: "2px solid #262627",
        transform: "rotate(45deg)",
    },

    headerTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
    },

    headerRight: {
        position: "absolute",
        right: 16,
        top: 13,
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

    shareIcon: {
        fontSize: 16,
        lineHeight: "16px",
        color: "#262627",
        transform: "translateY(-1px)",
    },

    kebabDots: {
        width: 3,
        height: 3,
        borderRadius: "50%",
        backgroundColor: "#262627",
        boxShadow: "0 -6px 0 #262627, 0 6px 0 #262627",
    },

    main: {
        padding: "16px 16px 24px 16px",
    },

    profileTop: {
        display: "flex",
        alignItems: "center",
        gap: 16,
    },

    profileInfo: {
        display: "flex",
        flexDirection: "column",
        gap: 4,
    },

    name: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 600,
        color: "#262627",
    },

    subText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#72787F",
    },

    tabRow: {
        marginTop: 20,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        borderBottom: "1px solid #E8EBED",
    },

    tabBtn: {
        height: 44,
        border: "none",
        background: "transparent",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 600,
        color: "#262627",
        cursor: "pointer",
        position: "relative",
    },

    tabBtnActive: {
        color: "#FBE200",
        borderBottom: "3px solid #FBE200",
    },

    section: {
        marginTop: 20,
    },

    sectionTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 8,
    },

    sectionSubTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#262627",
        marginBottom: 12,
    },

    soldList: {
        display: "flex",
        gap: 12,
        overflowX: "auto",
        paddingBottom: 4,
        marginBottom: 24,
    },

    soldItem: {
        width: 100,
        height: 100,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
        flexShrink: 0,
        objectFit: "cover",
        display: "block",
    },

    keywordTitle: {
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 12,
    },

    tagList: {
        display: "flex",
        gap: 8,
        flexWrap: "wrap",
    },
    
    tagItem: {
        height: 28,
        padding: "0 12px",
        borderRadius: 20,
        backgroundColor: "rgba(251, 226, 0, 0.3)",
        border: "1px solid #FBE200",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 500,
        color: "#262627",
        whiteSpace: "nowrap",
        boxSizing: "border-box",
    },

    summaryBox: {
        width: "100%",
        maxWidth: 358,
        minHeight: 52,
        borderRadius: 12,
        backgroundColor: "#F7F8F9",
        padding: "10px 12px",
        boxSizing: "border-box",
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#262627",
        marginBottom: 20,
    },

    traitSection: {
        marginBottom: 20,
    },

    traitTitle: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 600,
        marginBottom: 8,
    },

    traitList: {
        display: "flex",
        flexDirection: "column",
        gap: 8,
    },

    traitRow: {
        display: "grid",
        gridTemplateColumns: "52px 1fr 24px",
        alignItems: "center",
        columnGap: 8,
    },

    traitLabel: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#262627",
    },

    traitBarWrap: {
        display: "flex",
        alignItems: "center",
    },

    traitBarBg: {
        width: "100%",
        height: 12,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
        overflow: "hidden",
    },

    traitBarFill: {
        height: "100%",
        borderRadius: 12,
    },

    traitValue: {
        fontSize: 11,
        lineHeight: "14px",
        fontWeight: 400,
        color: "#72787F",
        textAlign: "right",
    },
};