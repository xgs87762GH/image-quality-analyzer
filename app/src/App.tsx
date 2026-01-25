/**
 * 根组件
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MainLayout } from './components/layout/MainLayout'
import { HomePage } from './pages/HomePage'
import { ImageDetailPage } from './pages/ImageDetailPage'
import { StatisticsPage } from './pages/StatisticsPage'
import { DuplicatesPage } from './pages/DuplicatesPage'
import { TrashPage } from './pages/TrashPage'
import { SystemInfoPage } from './pages/SystemInfoPage'
import { SettingsPage } from './pages/SettingsPage'
import './styles/globals.css'

// 初始化 i18n
import './i18n'

// 创建 QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="image/:id" element={<ImageDetailPage />} />
            <Route path="stats" element={<StatisticsPage />} />
            <Route path="duplicates" element={<DuplicatesPage />} />
            <Route path="trash" element={<TrashPage />} />
            <Route path="system" element={<SystemInfoPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
