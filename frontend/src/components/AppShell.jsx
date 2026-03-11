import { Outlet, useLocation } from "react-router-dom";
import BottomNav from "./BottomNav";

export default function AppShell() {
    const { pathname } = useLocation();

    // ✅ 네비바 없어야 하는 화면들
    const hideBottomNav = pathname === "/category" || pathname === "/login";

    return (
        <div className="viewport">
            <div className="device">
                <div className={`screen ${hideBottomNav ? "no-bottom-nav" : ""}`}>
                    <Outlet />
                </div>

                {!hideBottomNav && <BottomNav />}
            </div>
        </div>
    );
}