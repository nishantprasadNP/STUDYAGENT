import { useHealth } from "@/hooks/useHealth";

type Tone = "green" | "amber" | "red" | "grey";

const DOT: Record<Tone, string> = {
  green: "bg-green-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
  grey: "bg-neutral-400",
};

export function HealthBadge() {
  const { data, isPending, isError } = useHealth();

  let tone: Tone;
  let label: string;
  if (isError) {
    tone = "red";
    label = "API offline";
  } else if (isPending) {
    tone = "grey";
    label = "Checking…";
  } else if (data.status === "ok") {
    tone = "green";
    label = "API ok";
  } else {
    tone = "amber";
    label = "Degraded";
  }

  return (
    <div className="flex items-center gap-2 text-xs text-neutral-600" role="status">
      <span className={`inline-block h-2 w-2 rounded-full ${DOT[tone]}`} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
