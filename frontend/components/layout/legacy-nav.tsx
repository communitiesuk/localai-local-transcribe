'use client'

import { NavButton } from '@/components/layout/nav-button'
import { FileText, Home, Settings, Users } from 'lucide-react'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useQuery } from '@tanstack/react-query'
import { UserRole, hasAnyRole } from '@/lib/utils'

export function LegacyNav() {
  const { data: user } = useQuery(getUserUsersMeGetOptions())

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
          {hasAnyRole(user?.roles, [
            UserRole.LOCAL_AUTHORITY_ADMIN,
            UserRole.MHCLG_SUPPORT_ADMIN,
          ]) && (
            <NavButton href="/user-management">
              <Users size="1rem" /> User Management
            </NavButton>
          )}
        </div>
      </div>
    </div>
  )
}
