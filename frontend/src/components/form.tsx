import type { ReactNode } from "react";

export const inputClass =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 " +
  "focus:border-neutral-500 focus:outline-none disabled:bg-neutral-100";

export function FieldError({ message, id }: { message?: string; id?: string }) {
  if (!message) return null;
  return (
    <p id={id} className="mt-1 text-xs text-red-600" role="alert">
      {message}
    </p>
  );
}

interface FieldProps {
  id: string;
  label: string;
  error?: string;
  hint?: ReactNode;
  children: ReactNode;
}

export function Field({ id, label, error, hint, children }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs font-medium text-neutral-700">
        {label}
      </label>
      {children}
      {hint && <p className="mt-1 text-xs text-neutral-500">{hint}</p>}
      <FieldError message={error} id={`${id}-error`} />
    </div>
  );
}

interface SaveBarProps {
  dirty: boolean;
  saving: boolean;
  formError?: string;
  children?: ReactNode;
}

export function SaveBar({ dirty, saving, formError, children }: SaveBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 border-t border-neutral-200 pt-4">
      <button
        type="submit"
        disabled={!dirty || saving}
        className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
      >
        {saving ? "Saving…" : "Save"}
      </button>
      {formError && (
        <span className="text-xs text-red-600" role="alert">
          {formError}
        </span>
      )}
      {children}
    </div>
  );
}
