import { Outlet } from "react-router-dom";

export default function ChatShell() {
    return (
        <div className="viewport">
            <div className="device">
                <div className="screen no-bottom-nav">
                    <Outlet />
                </div>
            </div>
        </div>
    );
}