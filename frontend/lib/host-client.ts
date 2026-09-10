"use client";

import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

let cachedHostId: Promise<string> | null = null;

export async function getClientAccessToken(): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) {
    throw new Error("ログインしていません");
  }
  return session.access_token;
}

export async function getClientHostId(): Promise<string> {
  if (!cachedHostId) {
    cachedHostId = (async () => {
      const token = await getClientAccessToken();
      const data = await apiFetch<{ status: string; host: { id: string } }>(
        "/api/me",
        token,
      );
      return data.host.id;
    })();
  }
  return cachedHostId;
}
