const config = {
  controlPlaneAPI: import.meta.env.VITE_APP_ENDPOINT,
  sentryEnabled: import.meta.env.VITE_SENTRY_ENABLED === "true",
  sentryArn: import.meta.env.VITE_APP_SENTRY || "",
};

export const isSentryEnabled = () => config.sentryEnabled;

export { config };
