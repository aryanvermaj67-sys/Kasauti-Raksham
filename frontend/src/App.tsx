import CustomerApp from './pages/CustomerApp.tsx'
import Reviewer from './pages/Reviewer.tsx'

export default function App() {
  const path = window.location.pathname
  if (path.startsWith('/console')) window.history.replaceState(null, '', '/reviewer')
  if (path.startsWith('/reviewer') || path.startsWith('/console')) return <Reviewer />
  if (!path.startsWith('/app')) window.history.replaceState(null, '', '/app' + window.location.search)
  return <CustomerApp />
}
