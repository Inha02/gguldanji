import { aiEngineClient } from "../services/aiEngineClient.js";

function getAxiosErrorStatus(err) {
  // axios: err.response?.status exists when remote responded
  return err?.response?.status;
}

function getAxiosErrorData(err) {
  return err?.response?.data;
}

export const aiHealth = async (req, res) => {
  try {
    const r = await aiEngineClient.get("/api/v1/health");
    return res.status(200).json(r.data);
  } catch (err) {
    const status = getAxiosErrorStatus(err);
    if (status) {
      return res.status(status).json({
        message: "ai-engine error",
        details: getAxiosErrorData(err)
      });
    }
    return res.status(502).json({
      message: "ai-engine is unreachable"
    });
  }
};

export const estimatePrice = async (req, res) => {
  try {
    const r = await aiEngineClient.post("/api/v1/estimate", req.body);
    return res.status(200).json(r.data);
  } catch (err) {
    const status = getAxiosErrorStatus(err);
    if (status) {
      return res.status(status).json({
        message: "ai-engine error",
        details: getAxiosErrorData(err)
      });
    }
    return res.status(502).json({
      message: "ai-engine is unreachable"
    });
  }
};

export const analyzeSellerProfile = async (req, res) => {
  try {
    const r = await aiEngineClient.post("/profiling/analyze", req.body);

    return res.status(200).json(r.data);
  } catch (err) {
    const status = getAxiosErrorStatus(err);

    if (status) {
      return res.status(status).json({
        message: "ai-engine error",
        details: getAxiosErrorData(err)
      });
    }

    return res.status(502).json({
      message: "ai-engine is unreachable"
    });
  }
};