import jwt from "jsonwebtoken";

const auth = (req, res, next) => {
  try {
    const header = req.headers.authorization;

    if (!header) {
      return res.status(401).json({ message: "토큰이 없습니다." });
    }

    // "Bearer 토큰값"
    const token = header.split(" ")[1];

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // req에 유저 정보 저장
    req.user = {
      id: decoded.userId
    };

    next();

  } catch (error) {
    console.error(error);
    return res.status(401).json({ message: "유효하지 않은 토큰입니다." });
  }
};
export default auth;