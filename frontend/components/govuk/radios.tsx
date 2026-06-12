'use client'

import { cn } from '@/lib/utils'
import {
  Children,
  createContext,
  forwardRef,
  isValidElement,
  useContext,
} from 'react'
import { GovukLabel } from './label'

type RadiosContextValue = {
  name: string
  selectedValue: string | undefined
  disabled: boolean
  setValue: (value: string) => void
  getItemIndex: (value: string) => number
}

const RadiosContext = createContext<RadiosContextValue | null>(null)

function useRadiosContext(componentName: string): RadiosContextValue {
  const ctx = useContext(RadiosContext)
  if (!ctx) {
    throw new Error(
      `${componentName} must be used inside <GovukRadios>. Place items as direct children of the radios group.`
    )
  }
  return ctx
}

// A single option for the `options` prop; `hint` is optional.
export type RadioOption = {
  label: React.ReactNode
  value: string
  hint?: React.ReactNode
}

type RadiosProps = {
  name: string
  value?: string
  onChange?: (value: string) => void
  disabled?: boolean
  className?: string
  // Primary API. Use GovukRadios.Item children for advanced cases instead.
  options?: RadioOption[]
  children?: React.ReactNode
} & Omit<
  React.HTMLAttributes<HTMLDivElement>,
  'className' | 'children' | 'onChange'
>

const GovukRadiosRoot = forwardRef<HTMLDivElement, RadiosProps>(
  function GovukRadiosRoot(
    { name, value, onChange, disabled, className, options, children, ...rest },
    ref
  ) {
    const setValue = (next: string) => onChange?.(next)

    // Canonical GDS ids: first item → `${name}`, rest → `${name}-2`, …
    const orderedValues = (() => {
      if (options) {
        return options.map((o) => o.value)
      }
      const out: string[] = []
      Children.forEach(children, (child) => {
        if (!isValidElement(child)) return
        if (child.type !== GovukRadiosItem) return
        const props = child.props as { value?: unknown }
        if (typeof props.value !== 'string') return
        if (!out.includes(props.value)) {
          out.push(props.value)
        }
      })
      return out
    })()

    const getItemIndex = (itemValue: string) => {
      const idx = orderedValues.indexOf(itemValue)
      return idx === -1 ? 0 : idx
    }

    const contextValue: RadiosContextValue = {
      name,
      selectedValue: value,
      disabled: Boolean(disabled),
      setValue,
      getItemIndex,
    }

    return (
      <RadiosContext.Provider value={contextValue}>
        <div {...rest} ref={ref} className={cn('govuk-radios', className)}>
          {options
            ? options.map((option) => (
                <GovukRadiosItem
                  key={option.value}
                  value={option.value}
                  hint={option.hint}
                >
                  {option.label}
                </GovukRadiosItem>
              ))
            : children}
        </div>
      </RadiosContext.Provider>
    )
  }
)

type ItemProps = {
  value: string
  id?: string
  hint?: React.ReactNode
  className?: string
  children: React.ReactNode
} & Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'value' | 'name' | 'type' | 'checked' | 'onChange' | 'disabled' | 'className'
>

function GovukRadiosItem({
  value,
  id,
  hint,
  className,
  children,
  ...rest
}: ItemProps) {
  const ctx = useRadiosContext('<GovukRadios.Item>')
  const index = ctx.getItemIndex(value)
  const resolvedId = id ?? (index === 0 ? ctx.name : `${ctx.name}-${index + 1}`)
  const hintId = `${resolvedId}-hint`

  return (
    <div className={cn('govuk-radios__item', className)}>
      <input
        {...rest}
        className="govuk-radios__input"
        id={resolvedId}
        name={ctx.name}
        type="radio"
        value={value}
        checked={ctx.selectedValue === value}
        onChange={(event) => {
          if (event.target.checked) {
            ctx.setValue(value)
          }
        }}
        disabled={ctx.disabled}
        aria-describedby={hint ? hintId : undefined}
      />
      <GovukLabel className="govuk-radios__label" htmlFor={resolvedId}>
        {children}
      </GovukLabel>
      {hint && (
        <div className="govuk-hint govuk-radios__hint" id={hintId}>
          {hint}
        </div>
      )}
    </div>
  )
}

type GovukRadiosComponent = typeof GovukRadiosRoot & {
  Item: typeof GovukRadiosItem
}

export const GovukRadios = GovukRadiosRoot as GovukRadiosComponent
GovukRadios.Item = GovukRadiosItem
