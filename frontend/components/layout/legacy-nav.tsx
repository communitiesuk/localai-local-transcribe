import { NavButton } from '@/components/layout/nav-button'
import { FileText, Home, Settings } from 'lucide-react'

export function LegacyNav() {
  return (
    <div className="header-grid w-full items-center border-b border-[var(--govuk-border-colour)] px-6 py-1">
      <div className="flex items-center" style={{ gridArea: 'nav' }}>
        <NavButton href="/">
          <Home size="1rem" /> Home
        </NavButton>
        <NavButton href="/templates">
          <FileText size="1rem" /> Templates
        </NavButton>
        <NavButton href="/settings">
          <Settings size="1rem" /> Settings
        </NavButton>
      </div>
    </div>
  )
}
