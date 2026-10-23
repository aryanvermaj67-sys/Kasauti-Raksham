import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// bundled font: Hindi renders with no CDN or network
import '@fontsource/noto-sans-devanagari/400.css'
import '@fontsource/noto-sans-devanagari/700.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
