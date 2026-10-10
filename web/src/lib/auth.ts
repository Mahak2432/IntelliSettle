import { config } from "@/lib/config";

const DEV_UID_KEY = "kk-dev-uid";

function devUid(): string {
  let uid: string | null = null;
  try {
    uid = localStorage.getItem(DEV_UID_KEY);
    if (!uid) {
      uid = crypto.randomUUID();
      localStorage.setItem(DEV_UID_KEY, uid);
    }
  } catch {
    uid ??= "dev-anonymous";
  }
  return uid;
}

let firebaseUser: Promise<import("firebase/auth").User> | null = null;

// Loaded lazily so low-end phones don't pay for the Firebase SDK until it's needed.
async function signedInUser() {
  firebaseUser ??= (async () => {
    const [{ initializeApp, getApps }, { getAuth, onAuthStateChanged, signInAnonymously }] = await Promise.all([
      import("firebase/app"),
      import("firebase/auth"),
    ]);
    const app = getApps()[0] ?? initializeApp(config.firebase);
    const auth = getAuth(app);
    const existing = await new Promise<import("firebase/auth").User | null>((resolve) => {
      const stop = onAuthStateChanged(auth, (user) => {
        stop();
        resolve(user);
      });
    });
    return existing ?? (await signInAnonymously(auth)).user;
  })();
  return firebaseUser;
}

export async function authHeaders(): Promise<Record<string, string>> {
  if (config.authMode === "dev") return { "X-Dev-Uid": devUid() };
  const user = await signedInUser();
  return { Authorization: `Bearer ${await user.getIdToken()}` };
}
