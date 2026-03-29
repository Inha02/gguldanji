import { useNavigate } from "react-router-dom";
import { CATEGORY_ITEMS } from "../constants/categories";

export default function Category() {
    const navigate = useNavigate();

    return (
        <div className="category-page">
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

            <div className="category-main">
                <div className="category-grid">
                    {CATEGORY_ITEMS.map((item) => (
                        <button
                            key={item.name}
                            className="category-item"
                            type="button"
                            onClick={() => navigate(`/?cat=${encodeURIComponent(item.name)}`)}
                        >
                            <div className="category-circle" aria-hidden="true">
                                <img
                                    src={item.icon}
                                    alt=""
                                    className="category-icon"
                                />
                            </div>

                            <div className="category-label">{item.name}</div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}