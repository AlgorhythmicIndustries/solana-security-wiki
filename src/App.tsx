import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { IncidentPage } from "./pages/IncidentPage";
import { TrendsPage } from "./pages/TrendsPage";
import { ChecklistPage } from "./pages/ChecklistPage";
import { VideosPage } from "./pages/VideosPage";
import { MiscResourcesPage } from "./pages/MiscResourcesPage";
import { SimdsPage } from "./pages/SimdsPage";
import { InvestigationsPage } from "./pages/InvestigationsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/incident/:id" element={<IncidentPage />} />
          <Route path="/investigations" element={<InvestigationsPage />} />
          <Route path="/trends" element={<TrendsPage />} />
          <Route path="/checklist" element={<ChecklistPage />} />
          <Route path="/videos" element={<VideosPage />} />
          <Route path="/resources" element={<MiscResourcesPage />} />
          <Route path="/simds" element={<SimdsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
