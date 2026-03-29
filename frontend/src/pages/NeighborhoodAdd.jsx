import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

export default function NeighborhoodAdd() {
  const navigate = useNavigate();
  const [mapUrl, setMapUrl] = useState("");
  const [townName, setTownName] = useState("위치 확인 중...");

  useEffect(() => {
    console.log("🚀 useEffect 실행됨");
    console.log("window.kakao:", window.kakao);
    console.log("window.kakao.maps:", window.kakao?.maps);
    console.log("window.kakao.maps.services:", window.kakao?.maps?.services);

    window.kakao.maps.load(() => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;

          // ✅ 지도 이미지 (네이버 그대로 유지)
          const url = `https://maps.apigw.ntruss.com/map-static/v2/raster-cors?w=400&h=270&center=${lng},${lat}&level=16&format=jpg&markers=type:d|size:mid|pos:${lng}%20${lat}&X-NCP-APIGW-API-KEY-ID=${import.meta.env.VITE_NAVER_MAP_KEY}`;

          setMapUrl(url);

          // 🔥 카카오 Geocoder 생성
          const geocoder = new window.kakao.maps.services.Geocoder();

          // 🔥 좌표 → 행정동 변환
          geocoder.coord2RegionCode(lng, lat, (result, status) => {
            if (status === window.kakao.maps.services.Status.OK) {
              console.log("카카오 결과:", result);

              // ✅ 행정동(H) 찾기
              const region = result.find((r) => r.region_type === "H");

              if (region) {
                setTownName(region.address_name);
              } else {
                setTownName(result[0].address_name);
              }
            } else {
              console.error("카카오 변환 실패");
              setTownName("위치 확인 실패");
            }
          });
        },
        (error) => {
          console.error("위치 권한 거부됨", error);
          setTownName("위치 권한 필요");
        },
      );
    });
  }, []);

  const handleSetLocation = async () => {
  try {
    const token = localStorage.getItem("token");

    const res = await fetch("http://localhost:4000/users/me/location", {
  method: "PATCH",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({
    location: townName,
  }),
});

    const data = await res.json();

    if (res.ok) {
      alert("동네 인증 완료!");
      navigate("/mypage");
    } else {
      alert(data.message || "실패");
    }
  } catch (error) {
    console.error(error);
    alert("에러 발생");
  }
};

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <button
          type="button"
          aria-label="뒤로가기"
          style={styles.backBtn}
          onClick={() => navigate("/neighborhoodmanage")}
        >
          <span style={styles.backIcon} />
        </button>

        <div style={styles.headerTitle}>동네 인증 관리</div>
      </div>

      {/* Main */}
      <div style={styles.main}>
        <div style={styles.sectionTitle}>현위치</div>

        <div style={styles.mapBox}>
          <div
            style={{
              ...styles.mapPlaceholder,
              backgroundImage: mapUrl ? `url(${mapUrl})` : "none",
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />
        </div>

        <div style={styles.locationText}>
          현재 위치는 <span style={styles.locationTown}>{townName}</span>이에요.
        </div>
      </div>

      {/* Bottom Button */}
      <div style={styles.bottomArea}>
        <button type="button" style={styles.addBtn} onClick={handleSetLocation}>
          현재 위치로 동네 인증하기
        </button>
      </div>
    </div>
  );
}

const styles = {
  page: {
    width: "100%",
    height: "100%",
    backgroundColor: "#FDFDFD",
    position: "relative",
    display: "flex",
    flexDirection: "column",
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
    flexShrink: 0,
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

  main: {
    flex: 1,
    padding: "16px 0 100px 0",
    boxSizing: "border-box",
  },

  sectionTitle: {
    fontSize: 16,
    lineHeight: "24px",
    fontWeight: 700,
    color: "#262627",
    padding: "0 16px",
    marginBottom: 12,
  },

  mapBox: {
    width: "100%",
    height: 270,
    backgroundColor: "#F7F8F9",
    overflow: "hidden",
  },

  mapPlaceholder: {
    width: "100%",
    height: "100%",
    backgroundColor: "#E8EBED",
  },

  locationText: {
    marginTop: 16,
    textAlign: "center",
    fontSize: 16,
    lineHeight: "24px",
    fontWeight: 400,
    color: "#262627",
  },

  locationTown: {
    fontWeight: 700,
  },

  bottomArea: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 12,
  },

  addBtn: {
    width: "100%",
    height: 48,
    borderRadius: 16,
    border: "none",
    backgroundColor: "#FBE200",
    color: "#262627",
    fontSize: 20,
    lineHeight: "28px",
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
  },
};
