import { NavButton } from '@/components/layout/nav-button'
import { FileText, Home, Settings } from 'lucide-react'

export function LegacyNav() {
  return (
    <div className="border-b border-[var(--govuk-border-colour)]">
      <div className="govuk-width-container">
        <div className="flex items-center py-1">
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
    </div>
  )
}
