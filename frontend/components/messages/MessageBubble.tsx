import { formatDateTime } from "./utils";

type Props = {
  align: "left" | "right";
  text: string;
  timestamp: string | null;
  label?: string;
  onEdit?: () => void;
};

export function MessageBubble({ align, text, timestamp, label, onEdit }: Props) {
  const isRight = align === "right";

  return (
    <div className={`flex flex-col ${isRight ? "items-end" : "items-start"}`}>
      {label && (
        <span className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
          {label}
        </span>
      )}
      <div
        className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm shadow-sm ${
          isRight
            ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
            : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
        }`}
      >
        {text}
      </div>
      <div className="mt-1 flex items-center gap-2 text-xs text-zinc-400 dark:text-zinc-500">
        <span>{formatDateTime(timestamp)}</span>
        {onEdit && (
          <button
            type="button"
            onClick={onEdit}
            className="underline decoration-dotted underline-offset-2 hover:text-zinc-600 dark:hover:text-zinc-300"
          >
            編集して送り直す
          </button>
        )}
      </div>
    </div>
  );
}
