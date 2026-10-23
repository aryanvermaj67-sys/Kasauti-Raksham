import BankApp from './pages/BankApp.tsx'
import Reviewer from './pages/Reviewer.tsx'

export default function App() {
  const path = window.location.pathname
  if (path.startsWith('/reviewer')) return <Reviewer />
  if (!path.startsWith('/app')) window.history.replaceState(null, '', '/app')
  return <BankApp />
}
