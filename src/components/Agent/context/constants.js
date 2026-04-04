export const MAX_SESSIONS = 50;

export const SENTRY_ENABLED = import.meta.env.VITE_SENTRY_ENABLED === "true";

const buildEndpoint = (path) => {
  if (!SENTRY_ENABLED) {
    return null;
  }
  // Lokale Sentry (Docker `td-sentry`, poort 8090): zet VITE_SENTRY_BASE_URL=http://localhost:8090
  const localBase = import.meta.env.VITE_SENTRY_BASE_URL;
  if (localBase) {
    const base = String(localBase).replace(/\/$/, "");
    return `${base}/${path}`;
  }
  if (!import.meta.env.VITE_APP_SENTRY) {
    return null;
  }
  return `https://bedrock-agentcore.${import.meta.env.VITE_COGNITO_REGION}.amazonaws.com/runtimes/${import.meta.env.VITE_APP_SENTRY}/${path}?qualifier=DEFAULT`;
};

export const API_ENDPOINT = buildEndpoint("invocations");
export const TOOLS_ENDPOINT = buildEndpoint("invocations");
export const SESSION_HISTORY_ENDPOINT = buildEndpoint("invocations");
export const SESSION_PREPARE_ENDPOINT = buildEndpoint("invocations");
export const SESSION_CLEAR_ENDPOINT = buildEndpoint("invocations");
