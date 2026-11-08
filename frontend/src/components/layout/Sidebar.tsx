import { NavLink } from "react-router";

import { HealthBadge } from "@/components/HealthBadge";

const LINKS = [
  { to: "/", label: "Today" },
  { to: "/plan", label: "Plan" },
  { to: "/checkin", label: "Check-in" },
  { to: "/analytics", label: "Analytics" },
  { to: "/revisions", label: "Revisions" },
  { to: "/reports", label: "Reports" },
  { to: "/profile", label: "Profile" },
  { to: "/settings", label: "Settings" },
  { to: "/topics", label: "Topics" },
] as const;

export function Sidebar() {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-neutral-200 bg-white">
      <div className="px-5 py-4 text-base font-semibold text-neutral-900">StudyPilot AI</div>
      <nav className="flex-1 space-y-0.5 px-3">
        {LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-neutral-200 px-5 py-3">
        <HealthBadge />
      </div>
    </aside>
  );
}
