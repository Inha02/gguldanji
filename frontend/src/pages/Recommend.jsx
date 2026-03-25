import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import HomeHeader from "../components/HomeHeader";
import ProductCard from "../components/ProductCard";

const mock = [
    { id: 1, title: "아이폰 14 Pro 256GB", price: "950,000", location: "서울 강남구", time: "2시간 전", tag: "저가", category: "디지털기기" },
    { id: 2, title: "에어팟 프로 2세대(정품)", price: "210,000", location: "서울 서초구", time: "3시간 전", tag: "저가", category: "디지털기기" },
    { id: 3, title: "이케아 스탠드 조명", price: "15,000", location: "서울 강남구", time: "4시간 전", tag: "상가", category: "가구/인테리어" },
    { id: 4, title: "원목 책상", price: "40,000", location: "서울 강남구", time: "7시간 전", tag: "적정", category: "가구/인테리어" },
    { id: 5, title: "검은 색 니트 조끼", price: "30,000", location: "서울 강남구", time: "8시간 전", tag: "적정", category: "여성의류" },
    { id: 6, title: "검은 색 나이키 신발", price: "90,000", location: "서울 서초구", time: "11시간 전", tag: "상가", category: "패션잡화" },
];

export default function Recommend() {
    const navigate = useNavigate();

    const selectedCategories = JSON.parse(
        localStorage.getItem("interestCategories") || "[]"
    );

    const filteredList = useMemo(() => {
        if (selectedCategories.length === 0) return mock;

        return mock.filter((item) =>
            selectedCategories.includes(item.category)
        );
    }, [selectedCategories]);

    return (
        <>
            <HomeHeader showBell={true} onMenuClick={() => navigate("/category")} />

            <div style={styles.page}>
                <div style={styles.grid}>
                    {filteredList.map((item) => (
                        <ProductCard key={item.id} item={item} />
                    ))}
                </div>
            </div>
        </>
    );
}

const styles = {
    page: {
        padding: 16,
        backgroundColor: "#F7F8F9",
        minHeight: "100%",
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        columnGap: 12,
        rowGap: 10,
    },
};