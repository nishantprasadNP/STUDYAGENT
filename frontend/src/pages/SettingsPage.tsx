import { useState, type FormEvent } from "react";

import { fieldErrorsOf } from "@/api/client";
import type { SettingsOut, SettingsPatch } from "@/api/types";
import { Field, SaveBar, inputClass } from "@/components/form";
import { formErrorOf } from "@/lib/forms";
import { useSettings, useUpdateSettings } from "@/hooks/useSettings";

type SettingKey = keyof SettingsPatch & keyof SettingsOut;

interface SettingDef {
  key: SettingKey;
  label: string;
  help: string;
  kind: "ratio" | "float" | "int";
}

const GROUPS: { title: string; settings: SettingDef[] }[] = [
  {
    title: "Behind / ahead",
    settings: [
      {
        key: "behind_completion_threshold",
        label: "Behind completion threshold",
        help: "Daily completion below this marks the day as behind (0–1).",
        kind: "ratio",
      },
      {
        key: "behind_carryover_count",
        label: "Behind carry-over count",
        help: "This many carried-over tasks also marks you as behind.",
        kind: "int",
      },
      {
        key: "ahead_completion_threshold",
        label: "Ahead completion threshold",
        help: "Daily completion at or above this marks the day as ahead (0–1).",
        kind: "ratio",
      },
    ],
  },
  {
    title: "Weak topics",
    settings: [
      {
        key: "weak_topic_min_problems",
        label: "Minimum problems",
        help: "Problems attempted before a topic can be judged weak.",
        kind: "int",
      },
      {
        key: "weak_topic_solve_ratio",
        label: "Solve ratio",
        help: "Solved ÷ attempted below this flags the topic as weak (0–1).",
        kind: "ratio",
      },
      {
        key: "weak_topic_difficult_ratio",
        label: "Difficult ratio",
        help: "Share of sessions rated difficult above this flags the topic as weak (0–1).",
        kind: "ratio",
      },
    ],
  },
  {
    title: "Planning",
    settings: [
      {
        key: "max_daily_overbook_ratio",
        label: "Max daily overbook ratio",
        help: "Planned minutes may reach this multiple of the day's availability.",
        kind: "float",
      },
      {
        key: "max_topics_per_day",
        label: "Max topics per day",
        help: "Upper limit on distinct topics scheduled on one day.",
        kind: "int",
      },
    ],
  },
  {
    title: "Revisions & check-ins",
    settings: [
      {
        key: "revision_expiry_hours",
        label: "Revision expiry (hours)",
        help: "Unanswered schedule revisions expire after this many hours.",
        kind: "int",
      },
      {
        key: "outstanding_checkin_days",
        label: "Outstanding check-in days",
        help: "Missed check-ins older than this many days are marked unreported.",
        kind: "int",
      },
    ],
  },
];

const ALL: SettingDef[] = GROUPS.flatMap((g) => g.settings);

type Draft = Record<SettingKey, string>;

function toDraft(s: SettingsOut): Draft {
  return Object.fromEntries(ALL.map((d) => [d.key, String(s[d.key])])) as Draft;
}

function buildPatch(draft: Draft, s: SettingsOut): SettingsPatch {
  const patch: Record<string, number | null> = {};
  for (const { key } of ALL) {
    const raw = draft[key].trim();
    const value = raw === "" ? null : Number(raw);
    if (value !== s[key]) patch[key] = value;
  }
  return patch as SettingsPatch;
}

function SettingsForm({
  settings,
  saved,
  onSaved,
}: {
  settings: SettingsOut;
  saved: boolean;
  onSaved: (saved: boolean) => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(settings));
  const mutation = useUpdateSettings();
  const patch = buildPatch(draft, settings);
  const dirty = Object.keys(patch).length > 0;
  const errors = fieldErrorsOf(mutation.error);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!dirty) return;
    mutation.mutateAsync(patch).then(
      () => onSaved(true),
      () => undefined,
    );
  }

  return (
    <form onSubmit={onSubmit} className="max-w-3xl space-y-6" noValidate>
      {GROUPS.map((group) => (
        <fieldset key={group.title} className="rounded-md border border-neutral-200 bg-white p-4">
          <legend className="px-1 text-sm font-semibold text-neutral-900">{group.title}</legend>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {group.settings.map((def) => (
              <Field
                key={def.key}
                id={def.key}
                label={def.label}
                hint={def.help}
                error={errors[def.key]}
              >
                <input
                  id={def.key}
                  type="number"
                  step={def.kind === "int" ? 1 : 0.05}
                  min={def.kind === "int" ? 1 : 0}
                  max={def.kind === "ratio" ? 1 : undefined}
                  className={inputClass}
                  value={draft[def.key]}
                  onChange={(e) => {
                    setDraft((d) => ({ ...d, [def.key]: e.target.value }));
                    if (saved) onSaved(false);
                  }}
                />
              </Field>
            ))}
          </div>
        </fieldset>
      ))}
      <SaveBar
        dirty={dirty}
        saving={mutation.isPending}
        formError={formErrorOf(mutation.error, errors)}
      >
        {saved && (
          <span className="text-xs text-green-700" role="status">
            Saved
          </span>
        )}
      </SaveBar>
    </form>
  );
}

export default function SettingsPage() {
  const { data, isPending, isError, error } = useSettings();
  const [saved, setSaved] = useState(false);

  return (
    <section>
      <h1 className="text-xl font-semibold text-neutral-900">Settings</h1>
      <p className="mt-1 mb-4 text-neutral-500">Thresholds the planner and check-ins use.</p>
      {isPending && <p className="text-neutral-500">Loading…</p>}
      {isError && <p className="text-red-600">Could not load settings: {error.message}</p>}
      {data && (
        <SettingsForm key={data.updated_at} settings={data} saved={saved} onSaved={setSaved} />
      )}
    </section>
  );
}
