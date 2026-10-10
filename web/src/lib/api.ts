import { authHeaders } from "@/lib/auth";
import { config } from "@/lib/config";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

type Options = Omit<RequestInit, "body"> & { json?: unknown; form?: FormData };

export async function api<T>(path: string, { json, form, headers, ...init }: Options = {}): Promise<T> {
  const response = await fetch(`${config.apiBase}${path}`, {
    ...init,
    headers: {
      ...(await authHeaders()),
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: json !== undefined ? JSON.stringify(json) : form,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {}
    throw new ApiError(detail, response.status);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const fetcher = <T,>(path: string) => api<T>(path);

/** Image URLs need auth headers, so fetch them as blobs. */
export async function authedImageUrl(path: string): Promise<string> {
  const response = await fetch(`${config.apiBase}${path}`, { headers: await authHeaders() });
  if (!response.ok) throw new ApiError("Image unavailable", response.status);
  return URL.createObjectURL(await response.blob());
}
