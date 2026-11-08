import type { FieldErrors } from "@/api/client";

/** Message for the save bar: generic when fields are highlighted, else the error itself. */
export function formErrorOf(error: Error | null, fields: FieldErrors): string | undefined {
  if (!error) return undefined;
  const mapped = Object.keys(fields).filter((k) => k !== "");
  return mapped.length > 0 ? "Please fix the highlighted fields." : error.message;
}
