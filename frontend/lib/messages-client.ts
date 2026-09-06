// 実API接続。仕様: backend/app/api/routes/messages.py
import { apiFetch } from "./api";
import { getClientAccessToken, getClientHostId } from "./host-client";
import type { Message, MessageThread } from "./types";

async function authContext() {
  const [hostId, token] = await Promise.all([
    getClientHostId(),
    getClientAccessToken(),
  ]);
  return { hostId, token };
}

export async function listThreads(): Promise<MessageThread[]> {
  const { hostId, token } = await authContext();
  const data = await apiFetch<{ status: string; threads: MessageThread[] }>(
    `/api/messages/threads/${hostId}`,
    token,
  );
  return data.threads;
}

export async function getThread(
  airbnbThreadId: string,
): Promise<{ thread: MessageThread; messages: Message[] }> {
  const { hostId, token } = await authContext();
  const data = await apiFetch<{
    status: string;
    thread: MessageThread;
    messages: Message[];
  }>(`/api/messages/threads/${hostId}/${airbnbThreadId}`, token);
  return { thread: data.thread, messages: data.messages };
}

export async function setSkipAutoReply(
  airbnbThreadId: string,
  skip: boolean,
): Promise<MessageThread> {
  const { hostId, token } = await authContext();
  const data = await apiFetch<{ status: string; thread: MessageThread }>(
    `/api/messages/threads/${hostId}/${airbnbThreadId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify({ skip_auto_reply: skip }),
    },
  );
  return data.thread;
}

export async function sendMessage(
  airbnbThreadId: string,
  text: string,
): Promise<{ airbnb_thread_id: string; sent_text: string }> {
  const { hostId, token } = await authContext();
  return apiFetch(
    `/api/messages/threads/${hostId}/${airbnbThreadId}/send`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ text }),
    },
  );
}
