// 実API接続。仕様: backend/app/api/routes/messages.py
import { apiFetch, HOST_ID } from "./api";
import type { Message, MessageThread } from "./types";

export async function listThreads(): Promise<MessageThread[]> {
  const data = await apiFetch<{ status: string; threads: MessageThread[] }>(
    `/api/messages/threads/${HOST_ID}`,
  );
  return data.threads;
}

export async function getThread(
  airbnbThreadId: string,
): Promise<{ thread: MessageThread; messages: Message[] }> {
  const data = await apiFetch<{
    status: string;
    thread: MessageThread;
    messages: Message[];
  }>(`/api/messages/threads/${HOST_ID}/${airbnbThreadId}`);
  return { thread: data.thread, messages: data.messages };
}

export async function setSkipAutoReply(
  airbnbThreadId: string,
  skip: boolean,
): Promise<MessageThread> {
  const data = await apiFetch<{ status: string; thread: MessageThread }>(
    `/api/messages/threads/${HOST_ID}/${airbnbThreadId}`,
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
  return apiFetch(`/api/messages/threads/${HOST_ID}/${airbnbThreadId}/send`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}
