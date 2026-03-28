import { useNavigate } from "react-router-dom";
import { icons } from "../icons";

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

export default function Category() {
    const navigate = useNavigate();

    return (
        <div className="category-page">
            {/* Header */}
            <div className="category-header">
                <button
                    className="category-back"
                    type="button"
                    aria-label="뒤로가기"
                    onClick={() => navigate("/")}
                >
                    <span className="category-back-icon" />
                </button>

                <div className="category-title text-heading-3">카테고리</div>
            </div>

            {/* 메인부분 */}
            <div className="category-main">
                <div className="category-grid">
                    {categories.map((name) => (
                        <button
                            key={name}
                            className="category-item"
                            type="button"
                            onClick={() => navigate(`/?cat=${encodeURIComponent(name)}`)}
                        >
                            <div className="category-circle" aria-hidden="true">
                                <img
                                    src={icons[name] || icons["디지털기기"]}
                                    alt=""
                                    className="category-icon"
                                />
                            </div>

                            <div className="category-label">{name}</div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}