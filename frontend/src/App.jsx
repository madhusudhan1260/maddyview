import { Navigate, Route, Routes } from 'react-router-dom'
import { useApp } from './context/AppContext'
import Layout from './components/Layout'
import { ErrorNote, Loading } from './components/ui'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'
import PersonalFinance from './pages/PersonalFinance'
import Deposits from './pages/Deposits'
import Goals from './pages/Goals'
import Portfolio from './pages/Portfolio'
import SettingsPage from './pages/Settings'
import { MarketIntelligence, MutualFunds, PaperTrading, Stocks, Trading } from './pages/Planned'

export default function App() {
  const { auth, refreshAuth } = useApp()
  if (auth.loading) return <div className="p-8"><Loading label="Starting MaddyView…" /></div>
  if (auth.error)
    return (
      <div className="mx-auto max-w-md p-8">
        <ErrorNote error={{ message: 'Cannot reach the MaddyView API. Is the backend running on port 8040?' }} onRetry={refreshAuth} />
      </div>
    )
  if (!auth.user) return <AuthPage setup={auth.setupRequired} />
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="personal-finance" element={<PersonalFinance />} />
        <Route path="deposits" element={<Deposits />} />
        <Route path="goals" element={<Goals />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="mutual-funds" element={<MutualFunds />} />
        <Route path="stocks" element={<Stocks />} />
        <Route path="trading" element={<Trading />} />
        <Route path="paper-trading" element={<PaperTrading />} />
        <Route path="market-intelligence" element={<MarketIntelligence />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
