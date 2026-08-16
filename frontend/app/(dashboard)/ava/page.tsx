import { AvaSettingsForm } from "@/components/ava/AvaSettingsForm";
import { getSettings } from "@/lib/settings-client";

export default async function AvaSettingsPage() {
  const settings = await getSettings();

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <AvaSettingsForm initialSettings={settings} />
    </div>
  );
}
