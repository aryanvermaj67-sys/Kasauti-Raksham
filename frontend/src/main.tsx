import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// bundled fonts: Latin and Hindi render with no CDN or network
import '@fontsource/inter/400.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/noto-sans-devanagari/400.css'
import '@fontsource/noto-sans-devanagari/700.css'
import 'material-symbols/outlined.css' // the design's icon font, bundled (no Google Fonts)
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
