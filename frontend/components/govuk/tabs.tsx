'use client'

import { cn } from '@/lib/utils'
import React, { useEffect, useState } from 'react'

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
  labelledBy?: string
}

function Panel({ id, className, children, isActive, labelledBy }: PanelProps) {
  return (
    <div
      id={id}
      className={cn(
        'govuk-tabs__panel',
        !isActive && 'govuk-tabs__panel--hidden',
        className
      )}
      role="tabpanel"
      aria-labelledby={labelledBy}
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
    if (defaultTab && panelIds.includes(defaultTab)) {
      return defaultTab
    }
    return panelIds[0] ?? ''
  })

  const currentTab = isControlled ? controlledTab : internalTab

  const stableActiveTab = panelIds.includes(currentTab)
    ? currentTab
    : (panelIds[0] ?? '')

  const panelIdsString = panelIds.join('*')

  useEffect(() => {
    if (panelIds.length > 0 && !panelIds.includes(currentTab)) {
      onTabChange?.(panelIds[0])
    }
  }, [panelIdsString, currentTab, onTabChange])

  const handleTabChange = (id: string) => {
    if (!isControlled) setInternalTab(id)
    onTabChange?.(id)
  }

  const focusTab = (tabId: string) => {
    document.getElementById(`${id}-${tabId}-tab`)?.focus()
  }

  const selectTab = (tabId: string) => {
    handleTabChange(tabId)
    focusTab(tabId)
  }

  const handleTabKeyDown = (event: React.KeyboardEvent<HTMLAnchorElement>) => {
    const currentIndex = panelIds.indexOf(stableActiveTab)

    if (currentIndex === -1) {
      return
    }

    const previousIndex =
      currentIndex === 0 ? panelIds.length - 1 : currentIndex - 1
    const nextIndex =
      currentIndex === panelIds.length - 1 ? 0 : currentIndex + 1

    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault()
        selectTab(panelIds[previousIndex])
        break
      case 'ArrowRight':
        event.preventDefault()
        selectTab(panelIds[nextIndex])
        break
      case 'Home':
        event.preventDefault()
        selectTab(panelIds[0])
        break
      case 'End':
        event.preventDefault()
        selectTab(panelIds[panelIds.length - 1])
        break
      case ' ':
      case 'Enter':
        event.preventDefault()
        selectTab(stableActiveTab)
        break
    }
  }

  return (
    <div {...rest} id={id} className={cn('govuk-tabs', className)}>
      <h2 className="govuk-tabs__title">{title}</h2>
      <ul role="tablist" className="govuk-tabs__list">
        {panels.map((panel) => (
          <li
            key={panel.props.id}
            className={cn('govuk-tabs__list-item', {
              'govuk-tabs__list-item--selected':
                panel.props.id === stableActiveTab,
            })}
          >
            <a
              id={`${id}-${panel.props.id}-tab`}
              className="govuk-tabs__tab"
              href={`#${panel.props.id}`}
              onClick={(e) => {
                e.preventDefault()
                handleTabChange(panel.props.id)
              }}
              onKeyDown={handleTabKeyDown}
              role="tab"
              aria-selected={panel.props.id === stableActiveTab}
              aria-controls={panel.props.id}
              tabIndex={panel.props.id === stableActiveTab ? 0 : -1}
            >
              {panel.props.label}
            </a>
          </li>
        ))}
      </ul>
      {panels.map((panel) =>
        React.cloneElement(panel, {
          isActive: panel.props.id === stableActiveTab,
          labelledBy: `${id}-${panel.props.id}-tab`,
        })
      )}
    </div>
  )
}

GovukTabsBase.Panel = Panel

export const GovukTabs = GovukTabsBase
