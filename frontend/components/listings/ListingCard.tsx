import type { Listing, ListingStatus } from "@/lib/types";

const STATUS_LABEL: Record<ListingStatus, string> = {
  active: "公開中",
  pending_scrape: "同期待ち",
  inactive: "非公開",
};

const STATUS_BADGE_CLASS: Record<ListingStatus, string> = {
  active:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  pending_scrape:
    "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  inactive: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
};

function formatTime(time: string | null): string {
  return time ?? "未設定";
}

function formatLastScrapedAt(value: string | null): string {
  if (!value) return "未同期";
  return new Date(value).toLocaleString("ja-JP");
}

export function ListingCard({ listing }: { listing: Listing }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold leading-snug text-zinc-900 dark:text-zinc-100">
          {listing.title ?? "(タイトル未設定)"}
        </h3>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE_CLASS[listing.status]}`}
        >
          {STATUS_LABEL[listing.status]}
        </span>
      </div>

      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        {listing.address ?? "住所未設定"}
      </p>

      <dl className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-zinc-600 dark:text-zinc-300">
        <div>
          <dt className="text-zinc-400 dark:text-zinc-500">チェックイン</dt>
          <dd>{formatTime(listing.check_in_time)}</dd>
        </div>
        <div>
          <dt className="text-zinc-400 dark:text-zinc-500">チェックアウト</dt>
          <dd>{formatTime(listing.check_out_time)}</dd>
        </div>
        <div>
          <dt className="text-zinc-400 dark:text-zinc-500">最大人数</dt>
          <dd>{listing.max_guests != null ? `${listing.max_guests}名` : "未設定"}</dd>
        </div>
        <div>
          <dt className="text-zinc-400 dark:text-zinc-500">最終同期</dt>
          <dd>{formatLastScrapedAt(listing.last_scraped_at)}</dd>
        </div>
      </dl>
    </div>
  );
}
