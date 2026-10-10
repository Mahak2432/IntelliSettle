export const APP_NAME = { en: "IntelliSettle", hi: "IntelliSettle" } as const;

export const config = {
  apiBase: process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8080",
  // dev: local API trusts an X-Dev-Uid header. firebase: anonymous Firebase sign-in + ID tokens.
  authMode: (process.env.NEXT_PUBLIC_AUTH_MODE ?? "dev") as "dev" | "firebase",
  firebase: {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  },
};
