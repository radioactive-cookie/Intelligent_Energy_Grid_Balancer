import { Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import StrategyPage from './pages/StrategyPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/strategy" element={<StrategyPage />} />
    </Routes>
  );
}
