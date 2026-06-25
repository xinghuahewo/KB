export type ChatProvider = "bgp_fastapi_rag";

export type ServerEnv = {
  bgpRagBaseUrl: string;
  chatProvider: ChatProvider;
};

export function getServerEnv(env: NodeJS.ProcessEnv = process.env): ServerEnv {
  return {
    bgpRagBaseUrl: env.BGP_RAG_BASE_URL || "http://127.0.0.1:8000",
    chatProvider: "bgp_fastapi_rag",
  };
}
