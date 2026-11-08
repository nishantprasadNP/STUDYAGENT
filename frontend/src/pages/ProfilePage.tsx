import { useMemo, useState, type FormEvent } from "react";

import { fieldErrorsOf } from "@/api/client";
import type { ProfileOut, ProfilePatch, ProfileResponse, SkillLevel } from "@/api/types";
import { Field, FieldError, SaveBar, inputClass } from "@/components/form";
import { formErrorOf } from "@/lib/forms";
import { useProfile, useUpdateProfile } from "@/hooks/useProfile";

const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
type Weekday = (typeof WEEKDAYS)[number];

const DAY_LABELS: Record<Weekday, string> = {
  mon: "Mon",
  tue: "Tue",
  wed: "Wed",
  thu: "Thu",
  fri: "Fri",
  sat: "Sat",
  sun: "Sun",
};

const SKILL_LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced"];

const FIELD_LABELS: Record<string, string> = {
  name: "name",
  timezone: "timezone",
  goal_text: "goal",
  target_date: "target date",
  skill_level: "skill level",
  weekly_availability: "weekly availability",
  preferred_session_minutes: "preferred session length",
  checkin_time: "check-in time",
  reminder_time: "reminder time",
  preferences: "preferences",
};

interface Draft {
  name: string;
  timezone: string;
  goal_text: string;
  target_date: string;
  skill_level: string;
  weekly_availability: Record<Weekday, string>;
  preferred_session_minutes: string;
  checkin_time: string;
  reminder_time: string;
  preferences: string;
}

function toDraft(p: ProfileOut): Draft {
  return {
    name: p.name,
    timezone: p.timezone,
    goal_text: p.goal_text ?? "",
    target_date: p.target_date ?? "",
    skill_level: p.skill_level ?? "",
    weekly_availability: Object.fromEntries(
      WEEKDAYS.map((d) => [d, String(p.weekly_availability[d] ?? 0)]),
    ) as Record<Weekday, string>,
    preferred_session_minutes:
      p.preferred_session_minutes == null ? "" : String(p.preferred_session_minutes),
    checkin_time: p.checkin_time,
    reminder_time: p.reminder_time,
    preferences: JSON.stringify(p.preferences, null, 2),
  };
}

function minutes(value: string): number {
  return value.trim() === "" ? 0 : Number(value);
}

function hoursLabel(mins: number): string {
  if (!Number.isFinite(mins)) return "–";
  const h = mins / 60;
  return `${Number.isInteger(h) ? h : h.toFixed(1)} h`;
}

/** Diff the draft against the loaded profile; only changed fields go in the patch. */
function buildPatch(draft: Draft, p: ProfileOut): { patch: ProfilePatch; jsonError?: string } {
  const patch: ProfilePatch = {};
  if (draft.name !== p.name) patch.name = draft.name;
  if (draft.timezone !== p.timezone) patch.timezone = draft.timezone;

  const goal = draft.goal_text.trim() === "" ? null : draft.goal_text;
  if (goal !== (p.goal_text ?? null)) patch.goal_text = goal;

  const target = draft.target_date === "" ? null : draft.target_date;
  if (target !== (p.target_date ?? null)) patch.target_date = target;

  const skill = draft.skill_level === "" ? null : (draft.skill_level as SkillLevel);
  if (skill !== (p.skill_level ?? null)) patch.skill_level = skill;

  const week = Object.fromEntries(
    WEEKDAYS.map((d) => [d, minutes(draft.weekly_availability[d])]),
  ) as Record<Weekday, number>;
  if (WEEKDAYS.some((d) => week[d] !== (p.weekly_availability[d] ?? 0))) {
    patch.weekly_availability = week;
  }

  const session =
    draft.preferred_session_minutes.trim() === "" ? null : Number(draft.preferred_session_minutes);
  if (session !== (p.preferred_session_minutes ?? null)) patch.preferred_session_minutes = session;

  if (draft.checkin_time !== p.checkin_time) patch.checkin_time = draft.checkin_time;
  if (draft.reminder_time !== p.reminder_time) patch.reminder_time = draft.reminder_time;

  let jsonError: string | undefined;
  try {
    const parsed: unknown = JSON.parse(draft.preferences);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      jsonError = "Preferences must be a JSON object, e.g. {}";
    } else if (JSON.stringify(parsed) !== JSON.stringify(p.preferences)) {
      patch.preferences = parsed as Record<string, unknown>;
    }
  } catch {
    jsonError = "Invalid JSON";
  }
  return { patch, jsonError };
}

function timezoneOptions(current: string): string[] {
  const zones = Intl.supportedValuesOf("timeZone");
  return zones.includes(current) ? zones : [current, ...zones];
}

function CompletenessBanner({ missing }: { missing: string[] }) {
  return (
    <div
      className="mb-6 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900"
      role="status"
    >
      Finish your profile to create a study plan. Missing:{" "}
      {missing.map((f) => FIELD_LABELS[f] ?? f).join(", ")}
    </div>
  );
}

function SavedNotice({ result }: { result: ProfileResponse }) {
  return (
    <div className="text-xs text-green-700" role="status">
      Saved
      {result.changed_fields.length > 0 &&
        `: ${result.changed_fields.map((f) => FIELD_LABELS[f] ?? f).join(", ")}`}
      {result.plan_impact.availability_or_deadline_changed && (
        <span className="ml-2 text-amber-700">
          Your study plan may need a revision (available from Phase 5).
        </span>
      )}
    </div>
  );
}

interface ProfileFormProps {
  profile: ProfileOut;
  saved: ProfileResponse | null;
  onSaved: (result: ProfileResponse | null) => void;
}

function ProfileForm({ profile, saved, onSaved }: ProfileFormProps) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(profile));
  const mutation = useUpdateProfile();
  const zones = useMemo(() => timezoneOptions(profile.timezone), [profile.timezone]);

  const { patch, jsonError } = buildPatch(draft, profile);
  const dirty = Object.keys(patch).length > 0;
  const errors = fieldErrorsOf(mutation.error);
  const formError = formErrorOf(mutation.error, errors);

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((d) => ({ ...d, [key]: value }));
    if (saved) onSaved(null);
  }

  function setDay(day: Weekday, value: string) {
    set("weekly_availability", { ...draft.weekly_availability, [day]: value });
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!dirty || jsonError) return;
    mutation.mutateAsync(patch).then(onSaved, () => undefined);
  }

  const total = WEEKDAYS.reduce((sum, d) => sum + minutes(draft.weekly_availability[d]), 0);

  return (
    <form onSubmit={onSubmit} className="max-w-3xl space-y-5" noValidate>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field id="name" label="Name" error={errors.name}>
          <input
            id="name"
            className={inputClass}
            value={draft.name}
            onChange={(e) => set("name", e.target.value)}
          />
        </Field>
        <Field id="timezone" label="Timezone" error={errors.timezone}>
          <select
            id="timezone"
            className={inputClass}
            value={draft.timezone}
            onChange={(e) => set("timezone", e.target.value)}
          >
            {zones.map((z) => (
              <option key={z} value={z}>
                {z}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <Field id="goal_text" label="Goal" error={errors.goal_text}>
        <textarea
          id="goal_text"
          rows={3}
          className={inputClass}
          value={draft.goal_text}
          onChange={(e) => set("goal_text", e.target.value)}
        />
      </Field>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Field id="target_date" label="Target date" error={errors.target_date}>
          <input
            id="target_date"
            type="date"
            className={inputClass}
            value={draft.target_date}
            onChange={(e) => set("target_date", e.target.value)}
          />
        </Field>
        <Field id="skill_level" label="Skill level" error={errors.skill_level}>
          <select
            id="skill_level"
            className={inputClass}
            value={draft.skill_level}
            onChange={(e) => set("skill_level", e.target.value)}
          >
            <option value="">— Not set —</option>
            {SKILL_LEVELS.map((s) => (
              <option key={s} value={s}>
                {s[0].toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </Field>
        <Field
          id="preferred_session_minutes"
          label="Preferred session (minutes)"
          error={errors.preferred_session_minutes}
          hint="15–720, leave empty for no preference"
        >
          <input
            id="preferred_session_minutes"
            type="number"
            min={15}
            max={720}
            className={inputClass}
            value={draft.preferred_session_minutes}
            onChange={(e) => set("preferred_session_minutes", e.target.value)}
          />
        </Field>
      </div>

      <fieldset>
        <legend className="mb-2 text-xs font-medium text-neutral-700">
          Weekly availability (minutes per day)
        </legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {WEEKDAYS.map((d) => (
            <div key={d}>
              <label htmlFor={`avail-${d}`} className="block text-xs text-neutral-600">
                {DAY_LABELS[d]}
              </label>
              <input
                id={`avail-${d}`}
                type="number"
                min={0}
                max={720}
                className={inputClass}
                value={draft.weekly_availability[d]}
                onChange={(e) => setDay(d, e.target.value)}
              />
              <p className="mt-0.5 text-xs text-neutral-500">
                {minutes(draft.weekly_availability[d])} →{" "}
                {hoursLabel(minutes(draft.weekly_availability[d]))}
              </p>
              <FieldError message={errors[`weekly_availability.${d}`]} />
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-neutral-600">
          Weekly total: {total} min ({hoursLabel(total)})
        </p>
        <FieldError message={errors.weekly_availability} />
      </fieldset>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field id="checkin_time" label="Check-in time" error={errors.checkin_time}>
          <input
            id="checkin_time"
            type="time"
            className={inputClass}
            value={draft.checkin_time}
            onChange={(e) => set("checkin_time", e.target.value)}
          />
        </Field>
        <Field
          id="reminder_time"
          label="Reminder time"
          error={errors.reminder_time}
          hint="Must be later than check-in on the same day"
        >
          <input
            id="reminder_time"
            type="time"
            className={inputClass}
            value={draft.reminder_time}
            onChange={(e) => set("reminder_time", e.target.value)}
          />
        </Field>
      </div>

      <Field id="preferences" label="Preferences (JSON)" error={jsonError ?? errors.preferences}>
        <textarea
          id="preferences"
          rows={4}
          className={`${inputClass} font-mono`}
          value={draft.preferences}
          onChange={(e) => set("preferences", e.target.value)}
        />
      </Field>

      <SaveBar dirty={dirty && !jsonError} saving={mutation.isPending} formError={formError}>
        {saved && <SavedNotice result={saved} />}
      </SaveBar>
    </form>
  );
}

export default function ProfilePage() {
  const { data, isPending, isError, error } = useProfile();
  const [saved, setSaved] = useState<ProfileResponse | null>(null);

  return (
    <section>
      <h1 className="mb-4 text-xl font-semibold text-neutral-900">Profile</h1>
      {isPending && <p className="text-neutral-500">Loading…</p>}
      {isError && <p className="text-red-600">Could not load profile: {error.message}</p>}
      {data && (
        <>
          {!data.is_complete && <CompletenessBanner missing={data.missing_fields} />}
          {/* Remount on each save so the draft resets to the server's values. */}
          <ProfileForm key={data.updated_at} profile={data} saved={saved} onSaved={setSaved} />
        </>
      )}
    </section>
  );
}
