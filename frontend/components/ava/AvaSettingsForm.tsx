"use client";

import { useState } from "react";
import type {
  AvaSettings,
  CheckinOutPolicy,
  PriceNegotiationPolicy,
} from "@/lib/types";
import { updateSettings } from "@/lib/settings-client";

type Props = {
  initialSettings: AvaSettings;
};

type EditableSettings = Omit<AvaSettings, "host_id" | "updated_at">;

function toEditable(settings: AvaSettings): EditableSettings {
  const { host_id, updated_at, ...rest } = settings;
  void host_id;
  void updated_at;
  return rest;
}

export function AvaSettingsForm({ initialSettings }: Props) {
  const [settings, setSettings] = useState<EditableSettings>(() =>
    toEditable(initialSettings),
  );
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof EditableSettings>(
    key: K,
    value: EditableSettings[K],
  ) {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateSettings(settings);
      setSavedAt(Date.now());
      window.setTimeout(() => setSavedAt(null), 3000);
    } catch {
      setError("保存に失敗しました。もう一度お試しください。");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* ヘッダー */}
      {/* 将来拡張ポイント: 複数アシスタントを運用する場合はここにアシスタント切替UI(セレクトやタブ)を追加する */}
      <div className="flex items-center gap-4 border-b border-zinc-200 pb-6 dark:border-zinc-800">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-lg font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
          A
        </span>
        <div>
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Ava
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            ゲストメッセージに自動で返信するAIアシスタント
          </p>
        </div>
      </div>

      {/* 基本設定 */}
      <Section title="基本設定">
        <FieldRow
          label="自動返信を有効にする"
          htmlFor="auto_reply_enabled"
        >
          <Toggle
            id="auto_reply_enabled"
            checked={settings.auto_reply_enabled}
            onChange={(checked) => update("auto_reply_enabled", checked)}
          />
        </FieldRow>

        <FieldRow label="ポーリング間隔" htmlFor="poll_interval_minutes">
          <select
            id="poll_interval_minutes"
            value={settings.poll_interval_minutes}
            onChange={(e) =>
              update(
                "poll_interval_minutes",
                Number(e.target.value) as AvaSettings["poll_interval_minutes"],
              )
            }
            className="w-40 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          >
            <option value={3}>3分</option>
            <option value={10}>10分</option>
            <option value={15}>15分</option>
          </select>
        </FieldRow>

        <FieldRow label="応答遅延(分)" htmlFor="reply_delay_minutes">
          <input
            id="reply_delay_minutes"
            type="number"
            min={0}
            step={1}
            value={settings.reply_delay_minutes}
            onChange={(e) => {
              const raw = Math.floor(Number(e.target.value));
              update("reply_delay_minutes", Number.isFinite(raw) && raw >= 0 ? raw : 0);
            }}
            className="w-40 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
        </FieldRow>
      </Section>

      {/* チェックイン/アウト方針 */}
      <Section title="チェックイン/アウト方針">
        <FieldRow label="アーリーチェックイン">
          <PolicyRadioGroup
            name="early_checkin_policy"
            value={settings.early_checkin_policy}
            onChange={(value) => update("early_checkin_policy", value)}
          />
        </FieldRow>

        <FieldRow label="レイトチェックアウト">
          <PolicyRadioGroup
            name="late_checkout_policy"
            value={settings.late_checkout_policy}
            onChange={(value) => update("late_checkout_policy", value)}
          />
        </FieldRow>
      </Section>

      {/* 荷物預かり */}
      <Section title="荷物預かり">
        <FieldRow
          label="荷物預かり案内を自動送信する"
          htmlFor="luggage_storage_enabled"
        >
          <Toggle
            id="luggage_storage_enabled"
            checked={settings.luggage_storage_enabled}
            onChange={(checked) => update("luggage_storage_enabled", checked)}
          />
        </FieldRow>

        <div>
          <textarea
            id="luggage_storage_message"
            value={settings.luggage_storage_message}
            disabled={!settings.luggage_storage_enabled}
            onChange={(e) =>
              update("luggage_storage_message", e.target.value)
            }
            rows={4}
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:disabled:bg-zinc-950 dark:disabled:text-zinc-600"
          />
        </div>
      </Section>

      {/* 価格交渉 */}
      <Section title="価格交渉">
        <FieldRow label="値引き交渉への対応">
          <PriceNegotiationRadioGroup
            value={settings.price_negotiation_policy}
            onChange={(value) => update("price_negotiation_policy", value)}
          />
        </FieldRow>
      </Section>

      {/* Avaの振る舞い(自由記述) */}
      <Section title="Avaの振る舞い(自由記述)">
        <textarea
          id="custom_instructions"
          value={settings.custom_instructions ?? ""}
          onChange={(e) =>
            update("custom_instructions", e.target.value || null)
          }
          placeholder="Avaへの追加指示があれば入力してください"
          rows={4}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-600"
        />
      </Section>

      {/* 保存 */}
      <div className="flex items-center gap-3 border-t border-zinc-200 pt-6 dark:border-zinc-800">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {saving ? "保存中..." : "保存する"}
        </button>
        {savedAt && (
          <span className="text-sm text-emerald-600 dark:text-emerald-400">
            保存しました
          </span>
        )}
        {error && (
          <span className="text-sm text-red-600 dark:text-red-400">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h2>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  );
}

function FieldRow({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <label
        htmlFor={htmlFor}
        className="text-sm text-zinc-700 dark:text-zinc-300"
      >
        {label}
      </label>
      {children}
    </div>
  );
}

function Toggle({
  id,
  checked,
  onChange,
}: {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
        checked
          ? "bg-zinc-900 dark:bg-zinc-100"
          : "bg-zinc-300 dark:bg-zinc-700"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform dark:bg-zinc-900 ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

function PolicyRadioGroup({
  name,
  value,
  onChange,
}: {
  name: string;
  value: CheckinOutPolicy;
  onChange: (value: CheckinOutPolicy) => void;
}) {
  const options: { value: CheckinOutPolicy; label: string }[] = [
    { value: "flexible", label: "柔軟に対応する" },
    { value: "strict", label: "厳格に対応する" },
  ];

  return (
    <div className="flex gap-4">
      {options.map((option) => (
        <label
          key={option.value}
          className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300"
        >
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={value === option.value}
            onChange={() => onChange(option.value)}
            className="h-4 w-4 border-zinc-300 text-zinc-900 focus:ring-zinc-500 dark:border-zinc-700"
          />
          {option.label}
        </label>
      ))}
    </div>
  );
}

function PriceNegotiationRadioGroup({
  value,
  onChange,
}: {
  value: PriceNegotiationPolicy;
  onChange: (value: PriceNegotiationPolicy) => void;
}) {
  const options: { value: PriceNegotiationPolicy; label: string }[] = [
    { value: "decline", label: "常に丁重にお断りする" },
    { value: "defer_to_host", label: "ホスト確認が必要と伝える" },
  ];

  return (
    <div className="flex flex-col gap-2">
      {options.map((option) => (
        <label
          key={option.value}
          className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300"
        >
          <input
            type="radio"
            name="price_negotiation_policy"
            value={option.value}
            checked={value === option.value}
            onChange={() => onChange(option.value)}
            className="h-4 w-4 border-zinc-300 text-zinc-900 focus:ring-zinc-500 dark:border-zinc-700"
          />
          {option.label}
        </label>
      ))}
    </div>
  );
}
