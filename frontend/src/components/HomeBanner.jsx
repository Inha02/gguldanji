import { useNavigate } from "react-router-dom";
import bannerImage from "../icons/homebanner.svg";

export default function HomeBanner({ name = "OO" }) {
    const navigate = useNavigate();

    return (
        <button
            className="home-banner"
            type="button"
            onClick={() => navigate("/recommend")}
        >
            <img
                src={bannerImage}
                alt=""
                className="home-banner__image"
            />

            <div className="home-banner__content">
                <div className="home-banner__text">
                    <div className="home-banner__title">{name}님의 취향,</div>
                    <div className="home-banner__sub">곰곰이가 기억했어요</div>
                </div>

                <span className="home-banner__arrow" aria-hidden="true">
                    <ChevronRight />
                </span>
            </div>
        </button>
    );
}

function ChevronRight() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
                d="M10 6l6 6-6 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}