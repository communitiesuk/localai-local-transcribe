'use client'

import { cn } from '@/lib/utils'
import React, { useEffect, useRef, useState } from 'react'

type TabsProps = {
  id: string
  title?: string
  className?: string
  children: React.ReactNode
  activeTab?: string
  defaultTab?: string
  onTabChange?: (id: string) => void
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'id'>

type PanelProps = {
  id: string
  label: React.ReactNode
  className?: string
  children: React.ReactNode
  isActive?: boolean
}

function Panel({ id, className, children, isActive }: PanelProps) {
  return (
    <div
      id={id}
      className={cn(
        'govuk-tabs__panel',
        !isActive && 'govuk-tabs__panel--hidden',
        className
      )}
    >
      {children}
    </div>
  )
}

function GovukTabsBase({
  id,
  title = 'Contents',
  className,
  children,
  activeTab: controlledTab,
  defaultTab,
  onTabChange,
  ...rest
}: TabsProps) {
  const panels = React.Children.toArray(children).filter(
    (child): child is React.ReactElement<PanelProps> =>
      React.isValidElement(child) && child.type === Panel
  )

  const panelIds = panels.map((p) => p.props.id)

  const isControlled = controlledTab !== undefined

  const [internalTab, setInternalTab] = useState<string>(() => {
    if (defaultTab && panelIds.includes(defaultTab)) return defaultTab;
    return panelIds[0] ?? ''
  })

  const currentTab = isControlled ? controlledTab : internalTab

  const stableActiveTab = panelIds.includes(currentTab)
    ? currentTab
    : (panelIds[0] ?? '')

  useEffect(() => {
    if (panelIds.length === 0) {
      return
    }
    if (!panelIds.includes(currentTab)) {
      const fallback = panelIds[0]
      if (!isControlled) setInternalTab(fallback)
      onTabChange?.(fallback)
    }
  }, [panelIds.join('*'), currentTab, isControlled, onTabChange])

  const handleTabChange = (id: string) => {
    if (!isControlled) setInternalTab(id);
    onTabChange?.(id);
  }

  return (
    <div
      {...rest}
      id={id}
      data-module="govuk-tabs"
      className={cn('govuk-tabs', className)}
    >
      <h2 className="govuk-tabs__title">{title}</h2>
      <ul className="govuk-tabs__list">
        {panels.map((panel) => (
          <li
            key={panel.props.id}
            className={cn('govuk-tabs__list-item', {
              'govuk-tabs__list-item--selected':
                panel.props.id === stableActiveTab,
            })}
          >
            <a
              className="govuk-tabs__tab"
              href={`#${panel.props.id}`}
              onClick={(e) => {
                e.preventDefault()
                handleTabChange(panel.props.id)
              }}
            >
              {panel.props.label}
            </a>
          </li>
        ))}
      </ul>
      {panels.map((panel) =>
        React.cloneElement(panel, {
          isActive: panel.props.id === stableActiveTab,
        })
      )}
    </div>
  )
}

GovukTabsBase.Panel = Panel

export const GovukTabs = GovukTabsBase
