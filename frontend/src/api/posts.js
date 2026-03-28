import client from "./client";

export const getPosts = async () => {
    const response = await client.get("/posts");
    return response.data;
};

export const getPostDetail = async (id) => {
    const response = await client.get(`/posts/${id}`);
    return response.data;
};

export const createPost = async (data) => {
    const response = await client.post("/posts", data);
    return response.data;
};