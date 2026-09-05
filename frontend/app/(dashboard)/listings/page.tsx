import { ListingCard } from "@/components/listings/ListingCard";
import { getListings } from "@/lib/listings-client";

export default async function ListingsPage() {
  const listings = await getListings();

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          リスティング一覧
        </h1>
        <button
          type="button"
          disabled
          title="BE実装後に接続予定"
          className="cursor-not-allowed rounded-md border border-zinc-300 bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-600"
        >
          同期
        </button>
      </div>

      {listings.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 p-8 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
          まだリスティングが同期されていません。
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}
