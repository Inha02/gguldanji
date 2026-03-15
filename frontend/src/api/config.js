/**
 * 백엔드 API 기본 URL
 * .env에 VITE_API_BASE_URL=http://localhost:4000 설정 가능
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:4000";

/** 카카오 로그인 시작 URL (백엔드로 이동 → 백엔드가 카카오로 리다이렉트) */
export const getKakaoLoginUrl = () => `${API_BASE_URL}/auth/kakao`;
