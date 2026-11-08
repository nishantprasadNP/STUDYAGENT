interface ChatPanelProps {
  onCollapse: () => void;
}

// TODO(phase-6): wire to the agent endpoint.
export function ChatPanel({ onCollapse }: ChatPanelProps) {
  return (
    <aside className="flex w-90 shrink-0 flex-col border-l border-neutral-200 bg-white">
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <h2 className="font-semibold text-neutral-900">StudyPilot agent</h2>
        <button
          type="button"
          onClick={onCollapse}
          className="rounded px-2 py-1 text-xs text-neutral-500 hover:bg-neutral-100"
          aria-label="Collapse chat panel"
        >
          Hide
        </button>
      </div>
      <div className="flex flex-1 items-center justify-center p-4 text-neutral-500">
        Agent arrives in Phase 6
      </div>
      <div className="border-t border-neutral-200 p-3">
        <input
          type="text"
          disabled
          placeholder="Ask StudyPilot…"
          className="w-full cursor-not-allowed rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-neutral-400"
        />
      </div>
    </aside>
  );
}
