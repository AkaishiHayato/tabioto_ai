import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";

export const verifySession = cache(async () => {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  return { user, accessToken: session!.access_token };
});

export const getHostId = cache(async () => {
  const { accessToken } = await verifySession();
  const data = await apiFetch<{ status: string; host: { id: string } }>(
    "/api/me",
    accessToken,
  );
  return data.host.id;
});

export const getAccessToken = cache(async () => {
  const { accessToken } = await verifySession();
  return accessToken;
});
