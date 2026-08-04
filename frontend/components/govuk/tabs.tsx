'use client'

import { cn } from '@/lib/utils'
import React from 'react'
import { useEffect, useRef } from 'react'

type TabsProps = {
  id: string
  title?: string
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'id'>

type PanelProps = {
  id: string
  label: React.ReactNode
  className?: string
  children: React.ReactNode
  _index?: number
}

function Panel({ id, className, children, _index }: PanelProps) {
  return (
    <div
      id={id}
      className={cn(
        'govuk-tabs__panel',
        _index !== 0 && 'govuk-tabs__panel--hidden',
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
  ...rest
}: TabsProps) {
  const wrappedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    import('govuk-frontend')
      .then(({ initAll }) => {
        if (!cancelled && wrappedRef.current) {
          initAll(wrappedRef.current)
        }
      })
      .catch((error) => {
        console.error('Error loading govuk-frontend:', error)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const panels = React.Children.toArray(children).filter(
    React.isValidElement
  ) as React.ReactElement<PanelProps>[]

  return (
    <div ref={wrappedRef}>
      <div
        {...rest}
        id={id}
        className={cn('govuk-tabs', className)}
        data-module="govuk-tabs"
      >
        <h2 className="govuk-tabs__title">{title}</h2>
        <ul className="govuk-tabs__list">
          {panels.map((panel, index) => (
            <li
              key={panel.props.id}
              className={cn('govuk-tabs__list-item', {
                'govuk-tabs__list-item--selected': index === 0,
              })}
            >
              <a className="govuk-tabs__tab" href={`#${panel.props.id}`}>
                {panel.props.label}
              </a>
            </li>
          ))}
        </ul>
        {panels.map((panel, index) =>
          React.cloneElement(panel, { _index: index })
        )}
      </div>
    </div>
  )
}

GovukTabsBase.Panel = Panel

export const GovukTabs = GovukTabsBase
