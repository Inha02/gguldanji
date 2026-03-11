export default function HomeHeader({ showBell = true, onMenuClick }) {
    return (
        <header className="home-header">
            <button className="icon-btn" aria-label="메뉴" onClick={onMenuClick}>
                <HamburgerIcon />
            </button>

            <div className="brand">
                <span className="brand-title">꿀단지</span>
            </div>

            <div className="header-right" style={{ width: 80, justifyContent: "flex-end" }}>
                {showBell && (
                    <button className="icon-btn" aria-label="알림">
                        <BellIcon />
                    </button>
                )}
                <button className="icon-btn" aria-label="검색">
                    <SearchIcon />
                </button>
            </div>
        </header>
    );
}


function HamburgerIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

function BellIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
                d="M18 8a6 6 0 10-12 0c0 7-3 7-3 7h18s-3 0-3-7"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinejoin="round"
            />
            <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

function SearchIcon() {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
            <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}
