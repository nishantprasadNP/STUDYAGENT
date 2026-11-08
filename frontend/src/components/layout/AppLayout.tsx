import { useState } from "react";
import { Outlet } from "react-router";

import { ChatPanel } from "@/components/layout/ChatPanel";
import { Sidebar } from "@/components/layout/Sidebar";

export function AppLayout() {
  const [chatOpen, setChatOpen] = useState(true);

  return (
    <div className="flex h-screen bg-neutral-50 text-sm text-neutral-800">
      <Sidebar />
      <main className="relative flex-1 overflow-y-auto px-8 py-6">
        {!chatOpen && (
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            className="absolute top-4 right-4 rounded-md border border-neutral-200 bg-white px-3 py-1.5 text-xs text-neutral-700 hover:bg-neutral-100"
          >
            Open agent
          </button>
        )}
        <Outlet />
      </main>
      {chatOpen && <ChatPanel onCollapse={() => setChatOpen(false)} />}
    </div>
  );
}
