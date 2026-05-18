import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { App } from './App'
import { ResultPage } from './pages/ResultPage'
import './index.css'

const rootEl = document.getElementById('root')
if (rootEl) {
  createRoot(rootEl).render(
    <StrictMode>
      <BrowserRouter>
        <Routes>
          <Route element={<App />} path="/" />
          <Route element={<ResultPage />} path="/r/:publicId" />
        </Routes>
      </BrowserRouter>
    </StrictMode>,
  )
}
