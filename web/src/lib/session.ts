import { api } from "@/lib/api";

const ROLE_KEY = "kk-role";

export async function startFarmerSession(farmerId: string) {
  await api("/api/session", { method: "POST", json: { role: "farmer", farmer_id: farmerId } });
  remember("farmer");
}

export async function startOfficerSession() {
  await api("/api/session", { method: "POST", json: { role: "reviewer" } });
  remember("reviewer");
}

function remember(role: string) {
  try {
    localStorage.setItem(ROLE_KEY, role);
  } catch {}
}
