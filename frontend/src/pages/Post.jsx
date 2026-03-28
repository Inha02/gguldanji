import { useState } from "react";
import { useNavigate } from "react-router-dom";

const categories = [
    "디지털기기",
    "가구/인테리어",
    "출산/유아동",
    "여성의류",
    "패션잡화",
    "남성의류",
    "가전제품",
    "생활용품",
    "스포츠/레저",
    "취미/게임",
    "뷰티/미용",
    "반려동물용품",
    "식품",
    "도서",
    "티켓/교환권",
    "기타 중고물품",
];

const conditions = ["S급", "A급", "B급", "C급", "부품용"];

export default function Post() {
    const navigate = useNavigate();

    const [category, setCategory] = useState("");
    const [categoryOpen, setCategoryOpen] = useState(false);
    const [title, setTitle] = useState("");
    const [price, setPrice] = useState("");
    const [condition, setCondition] = useState("");
    const [options, setOptions] = useState({
        정품박스: false,
        부속품: false,
        하자없음: false,
        네고가능: false,
    });
    const [description, setDescription] = useState("");
    const [brand, setBrand] = useState("");
    const [model, setModel] = useState("");

    const [locationOpen, setLocationOpen] = useState(false);
    const [selectedTown, setSelectedTown] = useState(null);
    const verifiedTowns = JSON.parse(localStorage.getItem("verifiedTowns") || "[]");

    const toggleOption = (key) => {
        setOptions((prev) => ({
            ...prev,
            [key]: !prev[key],
        }));
    };


    const handleSubmitPost = () => {
        const newItem = {
            id: Date.now(),
            title: title || "제목 없음",
            price: price || "0",
            category: category || "기타 중고물품",
            time: "방금 전",
            location: selectedTown?.name || "위치 미설정",
            description: description || "상품 설명이 없습니다.",
            tag: "적정",
            liked: false,
            images: [1, 2, 3],
            seller: {
                nickname: "서초구 불주먹",
                town: selectedTown?.name || "서울 서초구 방배1동",
            },
            guideMin: 600000,
            guideMax: 850000,
            sellerAnalysis: null,
        };

        navigate(`/product/${newItem.id}`, { state: { item: newItem } });
    };

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

                <div style={styles.headerTitle}>판매글 작성</div>
            </div>

            {/* Main */}
            <div style={styles.main}>
                {/* 사진 등록 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>사진 등록</div>
                    <div style={styles.sectionSub}>
                        사진은 최대 4개까지 등록 가능합니다.
                    </div>

                    <div style={styles.photoRow}>
                        <button type="button" style={styles.photoAddBox}>
                            <PlusIcon />
                        </button>

                        {[1, 2, 3].map((item) => (
                            <div key={item} style={styles.photoBox} />
                        ))}
                    </div>
                </section>

                {/* 카테고리 선택 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>카테고리 선택</div>
                    <div style={styles.sectionSub}>
                        무료로 나눔할 경우, ’기타 중고물품‘으로 선택해 주세요.
                    </div>

                    <div style={styles.dropdownWrap}>
                        <button
                            type="button"
                            style={styles.dropdownBtn}
                            onClick={() => setCategoryOpen((prev) => !prev)}
                        >
                            <span
                                style={{
                                    ...styles.dropdownText,
                                    color: category ? "#262627" : "#9EA4AA",
                                }}
                            >
                                {category || "카테고리를 선택해 주세요."}
                            </span>
                            <span style={styles.dropdownArrow}>⌄</span>
                        </button>

                        {categoryOpen && (
                            <div style={styles.dropdownMenu}>
                                {categories.map((item) => (
                                    <button
                                        key={item}
                                        type="button"
                                        style={styles.dropdownItem}
                                        onClick={() => {
                                            setCategory(item);
                                            setCategoryOpen(false);
                                        }}
                                    >
                                        {item}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </section>

                {/* 제목 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>제목</div>
                    <input
                        className="post-placeholder"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="제목을 입력해 주세요."
                        style={styles.input}
                    />
                </section>

                {/* 가격 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>가격</div>
                    <div style={styles.priceRow}>
                        <input
                            className="post-placeholder"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            placeholder="가격을 입력해 주세요."
                            style={styles.priceInput}
                        />
                        <span style={styles.priceUnit}>원</span>
                    </div>
                </section>

                {/* 상태 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>상태</div>
                    <div style={styles.chipRow}>
                        {conditions.map((item) => (
                            <button
                                key={item}
                                type="button"
                                onClick={() => setCondition(item)}
                                style={{
                                    ...styles.conditionBtn,
                                    ...(condition === item
                                        ? styles.conditionBtnSelected
                                        : styles.conditionBtnUnselected),
                                }}
                            >
                                <span
                                    style={{
                                        ...styles.conditionText,
                                        color:
                                            condition === item ? "#FDFDFD" : "#262627",
                                    }}
                                >
                                    {item}
                                </span>
                            </button>
                        ))}
                    </div>
                </section>

                {/* 옵션 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>옵션</div>
                    <div style={styles.sectionSub}>
                        해당 사항이 있을 때만 선택해 주세요. (복수 선택 가능)
                    </div>

                    <div style={styles.optionList}>
                        <label style={styles.optionItem}>
                            <span style={styles.checkboxWrap}>
                                <input
                                    type="checkbox"
                                    checked={options.정품박스}
                                    onChange={() => toggleOption("정품박스")}
                                    style={styles.hiddenCheckbox}
                                />
                                <span
                                    style={{
                                        ...styles.customCheckbox,
                                        ...(options.정품박스 ? styles.checkedBox : {}),
                                    }}
                                />
                            </span>
                            <span style={styles.optionText}>정품박스</span>
                        </label>

                        <label style={styles.optionItem}>
                            <span style={styles.checkboxWrap}>
                                <input
                                    type="checkbox"
                                    checked={options.부속품}
                                    onChange={() => toggleOption("부속품")}
                                    style={styles.hiddenCheckbox}
                                />
                                <span
                                    style={{
                                        ...styles.customCheckbox,
                                        ...(options.부속품 ? styles.checkedBox : {}),
                                    }}
                                />
                            </span>
                            <span style={styles.optionText}>부속품</span>
                        </label>

                        <label style={styles.optionItem}>
                            <span style={styles.checkboxWrap}>
                                <input
                                    type="checkbox"
                                    checked={options.하자없음}
                                    onChange={() => toggleOption("하자없음")}
                                    style={styles.hiddenCheckbox}
                                />
                                <span
                                    style={{
                                        ...styles.customCheckbox,
                                        ...(options.하자없음 ? styles.checkedBox : {}),
                                    }}
                                />
                            </span>
                            <span style={styles.optionText}>하자없음</span>
                        </label>

                        <label style={styles.optionItem}>
                            <span style={styles.checkboxWrap}>
                                <input
                                    type="checkbox"
                                    checked={options.네고가능}
                                    onChange={() => toggleOption("네고가능")}
                                    style={styles.hiddenCheckbox}
                                />
                                <span
                                    style={{
                                        ...styles.customCheckbox,
                                        ...(options.네고가능 ? styles.checkedBox : {}),
                                    }}
                                />
                            </span>
                            <span style={styles.optionText}>네고 가능</span>
                        </label>
                    </div>
                </section>
                {/* 상품 설명 */}
                <section style={styles.section}>
                    <div style={styles.sectionTitle}>상품 설명</div>
                    <div style={styles.sectionSub}>
                        설명은 최대 000자까지 작성 가능합니다.
                    </div>

                    <textarea
                        className="post-placeholder"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="상품 설명을 작성해 주세요."
                        style={styles.descriptionBox}
                    />
                </section>

                {/* 상세 정보 */}
                <section style={styles.detailSection}>
                    <div style={styles.sectionTitle}>상세 정보</div>

                    <div style={styles.detailInputs}>
                        <input
                            className="post-placeholder"
                            value={brand}
                            onChange={(e) => setBrand(e.target.value)}
                            placeholder="브랜드명"
                            style={styles.detailInput}
                        />

                        <input
                            className="post-placeholder"
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            placeholder="모델명"
                            style={styles.detailInput}
                        />
                    </div>
                </section>
                
                {/* 거래 희망 장소 */}
                <section style={styles.locationSection}>
                    <div style={styles.sectionTitle}>거래 희망 장소</div>

                    {!selectedTown ? (
                        <div style={styles.locationDropdownWrap}>
                            <button
                                type="button"
                                style={styles.locationBtn}
                                onClick={() => setLocationOpen((prev) => !prev)}
                            >
                                <span style={styles.locationBtnText}>위치 추가하기</span>
                                <span style={styles.locationBtnArrow}>⌄</span>
                            </button>

                            {locationOpen && (
                                <div style={styles.locationDropdownMenu}>
                                    {verifiedTowns.length > 0 ? (
                                        verifiedTowns.map((town) => (
                                            <button
                                                key={town.id}
                                                type="button"
                                                style={styles.locationDropdownItem}
                                                onClick={() => {
                                                    setSelectedTown(town);
                                                    setLocationOpen(false);
                                                }}
                                            >
                                                {town.name}
                                            </button>
                                        ))
                                    ) : (
                                        <div style={styles.locationDropdownEmpty}>
                                            인증된 동네가 없습니다.
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={styles.selectedTownList}>
                            <div style={styles.selectedTownCard}>
                                <div style={styles.selectedTownTop}>
                                    <div style={styles.selectedTownName}>{selectedTown.name}</div>

                                    <button
                                        type="button"
                                        style={styles.selectedTownDelete}
                                        onClick={() => setSelectedTown(null)}
                                    >
                                        삭제
                                    </button>
                                </div>

                                <div style={styles.selectedTownMap}>
                                    <div style={styles.selectedTownMapPlaceholder} />
                                </div>
                            </div>
                        </div>
                    )}
                </section>

                <div
                    style={{
                        ...styles.submitArea,
                        marginTop: selectedTown ? 19 : 28,
                    }}
                >
                    <button type="button" style={styles.submitBtn} onClick={handleSubmitPost}>
                        등록하기
                    </button>
                </div>
            </div>
        </div>
    );
}

function PlusIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
                d="M12 5v14M5 12h14"
                stroke="#9EA4AA"
                strokeWidth="1.8"
                strokeLinecap="round"
            />
        </svg>
    );
}

const styles = {
    page: {
        width: "100%",
        height: "100%",
        backgroundColor: "#FDFDFD",
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
        overflowY: "auto",
        padding: "16px 16px 24px 16px",
        boxSizing: "border-box",
    },

    section: {
        marginBottom: 20,
    },

    sectionTitle: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 700,
        color: "#262627",
        marginBottom: 8,
    },

    sectionSub: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#9EA4AA",
        marginBottom: 12,
    },

    photoRow: {
        display: "flex",
        gap: 12,
    },

    photoAddBox: {
        width: 74,
        height: 74,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        display: "grid",
        placeItems: "center",
        padding: 0,
        cursor: "pointer",
    },

    photoBox: {
        width: 74,
        height: 74,
        borderRadius: 12,
        backgroundColor: "#E8EBED",
    },

    dropdownWrap: {
        position: "relative",
        width: "100%",
    },

    dropdownBtn: {
        width: "100%",
        height: 42,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 14px",
        boxSizing: "border-box",
        cursor: "pointer",
    },

    dropdownText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
    },

    dropdownArrow: {
        fontSize: 16,
        lineHeight: "16px",
        color: "#9EA4AA",
    },

    dropdownMenu: {
        position: "absolute",
        top: 46,
        left: 0,
        right: 0,
        backgroundColor: "#FDFDFD",
        border: "1px solid #C9CDD2",
        borderRadius: 12,
        boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
        zIndex: 10,
        maxHeight: 180,
        overflowY: "auto",
    },

    dropdownItem: {
        width: "100%",
        height: 42,
        border: "none",
        background: "transparent",
        textAlign: "left",
        padding: "0 14px",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        cursor: "pointer",
    },

    input: {
        width: "100%",
        height: 42,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "0 14px",
        fontSize: 16,
        lineHeight: "24px",
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
    },

    priceRow: {
        display: "flex",
        alignItems: "center",
        gap: 8,
    },

    priceInput: {
        width: 358,
        height: 36,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "0 14px",
        fontSize: 16,
        lineHeight: "24px",
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
    },

    priceUnit: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#9EA4AA",
        whiteSpace: "nowrap",
    },

    chipRow: {
        display: "flex",
        gap: 8,
        flexWrap: "wrap",
    },

    conditionBtn: {
        height: 36,
        padding: "0 14px",
        borderRadius: 20,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        boxSizing: "border-box",
    },

    conditionBtnSelected: {
        backgroundColor: "#FBE200",
        border: "1px solid #FBE200",
    },

    conditionBtnUnselected: {
        backgroundColor: "#FDFDFD",
        border: "1px solid #C9CDD2",
    },

    conditionText: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        whiteSpace: "nowrap",
    },

    optionList: {
        display: "flex",
        flexDirection: "row",
        gap: 20,
        alignItems: "center",
    },

    optionItem: {
        display: "flex",
        alignItems: "center",
        gap: 8,
    },

    checkboxWrap: {
        position: "relative",
        width: 20,
        height: 20,
        display: "inline-block",
        flexShrink: 0,
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
        borderRadius: 4,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
    },

    checkedBox: {
        backgroundColor: "#FBE200",
        border: "1px solid #FBE200",
    },

    optionText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#262627",
        whiteSpace: "nowrap",
    },

    descriptionBox: {
        width: 358,
        height: 168,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "12px 14px",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
        resize: "none",
        fontFamily: "inherit",
    },

    detailSection: {
        marginTop: 28,
        marginBottom: 0,
    },

    detailInputs: {
        marginTop: 6,
        display: "flex",
        flexDirection: "column",
        gap: 6,
    },

    detailInput: {
        width: 358,
        height: 36,
        borderRadius: 12,
        border: "1px solid #C9CDD2",
        backgroundColor: "#FDFDFD",
        padding: "0 14px",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        outline: "none",
        boxSizing: "border-box",
    },

    locationSection: {
        marginTop: 45,
        marginBottom: 24,
    },

    locationBtn: {
        width: "100%",
        height: 36,
        marginTop: 8,
        background: "#454C53",
        border: "none",
        borderRadius: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 14px",
        boxSizing: "border-box",
        cursor: "pointer",
    },

    locationDropdownWrap: {
        position: "relative",
    },

    locationBtnText: {
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#FDFDFD",
    },

    locationBtnArrow: {
        fontSize: 20,
        lineHeight: "16px",
        color: "#FDFDFD",
    },

    locationDropdownMenu: {
        position: "absolute",
        top: "100%",
        left: 0,
        right: 0,
        marginTop: 0,
        backgroundColor: "#FDFDFD",
        border: "1px solid #C9CDD2",
        borderRadius: 12,
        zIndex: 20,
        overflow: "hidden",
    },

    locationDropdownItem: {
        width: "100%",
        height: 36,
        border: "none",
        background: "transparent",
        textAlign: "center",
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
        cursor: "pointer",
    },

    locationDropdownEmpty: {
        height: 36,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 14,
        lineHeight: "20px",
        fontWeight: 400,
        color: "#9EA4AA",
    },

    submitArea: {
        marginBottom: 10,
        backgroundColor: "#FDFDFD",
    },

    submitBtn: {
        width: "100%",
        height: 42,
        borderRadius: 16,
        border: "none",
        backgroundColor: "#FBE200",
        color: "#FDFDFD",
        fontSize: 20,
        lineHeight: "28px",
        fontWeight: 700,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    selectedTownList: {
        marginTop: 12,
        display: "flex",
        flexDirection: "column",
        gap: 12,
    },

    selectedTownCard: {
        width: "100%",
        borderRadius: 12,
        backgroundColor: "#FDFDFD",
        border: "1px solid #E8EBED",
        padding: 12,
        boxSizing: "border-box",
    },

    selectedTownTop: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 8,
    },

    selectedTownName: {
        fontSize: 16,
        lineHeight: "24px",
        fontWeight: 400,
        color: "#262627",
    },

    selectedTownDelete: {
        border: "none",
        background: "transparent",
        padding: 0,
        fontSize: 12,
        lineHeight: "16px",
        fontWeight: 400,
        color: "#9EA4AA",
        cursor: "pointer",
    },

    selectedTownMap: {
        width: "100%",
        height: 160,
        borderRadius: 12,
        overflow: "hidden",
        backgroundColor: "#F7F8F9",
    },

    selectedTownMapPlaceholder: {
        width: "100%",
        height: "100%",
        backgroundColor: "#E8EBED",
    },
};