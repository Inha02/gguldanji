import client from "./client";

export const getPriceEstimate = async (payload) => {
    const response = await client.post("/ai/price-estimate", payload);
    return response.data;
};