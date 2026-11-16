import { Route, Routes } from 'react-router-dom';
import CampaignsPage from './pages/CampaignsPage';
import EditorPage from './pages/EditorPage';

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<CampaignsPage />} />
        <Route path="/campaigns/:id" element={<EditorPage />} />
      </Routes>
    </div>
  );
}
