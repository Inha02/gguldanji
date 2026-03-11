import axios from "axios";

const baseURL = process.env.AI_ENGINE_URL;

if (!baseURL) {
  // eslint-disable-next-line no-console
  console.warn("⚠️ AI_ENGINE_URL is not set. AI routes will fail until configured.");
}

export const aiEngineClient = axios.create({
  baseURL,
  timeout: Number(process.env.AI_ENGINE_TIMEOUT_MS ?? 10_000),
  headers: {
    "Content-Type": "application/json"
  }
});

