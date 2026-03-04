FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4000
CMD ["node", "index.js"]

# node18 환경설정, 의존성 설차, 서버 실행