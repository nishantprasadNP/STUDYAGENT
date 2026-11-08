import { Route, Routes } from "react-router";

import { AppLayout } from "@/components/layout/AppLayout";
import AnalyticsPage from "@/pages/AnalyticsPage";
import CheckinPage from "@/pages/CheckinPage";
import NotFoundPage from "@/pages/NotFoundPage";
import PlanPage from "@/pages/PlanPage";
import ProfilePage from "@/pages/ProfilePage";
import ReportsPage from "@/pages/ReportsPage";
import RevisionsPage from "@/pages/RevisionsPage";
import SettingsPage from "@/pages/SettingsPage";
import TodayPage from "@/pages/TodayPage";
import TopicsPage from "@/pages/TopicsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<TodayPage />} />
        <Route path="plan" element={<PlanPage />} />
        <Route path="checkin" element={<CheckinPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="revisions" element={<RevisionsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="topics" element={<TopicsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
