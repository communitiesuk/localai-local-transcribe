'use client'

import { cn } from '@/lib/utils'
import {
  Children,
  createContext,
  forwardRef,
  isValidElement,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'

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

type RadiosProps = {
  name: string
  value?: string
  defaultValue?: string
  onChange?: (value: string) => void
  disabled?: boolean
  className?: string
  children: React.ReactNode
} & Omit<
  React.HTMLAttributes<HTMLDivElement>,
  'className' | 'children' | 'onChange' | 'defaultValue'
>

const GovukRadiosRoot = forwardRef<HTMLDivElement, RadiosProps>(function GovukRadiosRoot(
  {
    name,
    value,
    defaultValue,
    onChange,
    disabled,
    className,
    children,
    ...rest
  },
  ref
) {
  const isControlled = value !== undefined
  const [uncontrolledValue, setUncontrolledValue] = useState<
    string | undefined
  >(defaultValue)

  const selectedValue = isControlled ? value : uncontrolledValue

  const setValue = useCallback(
    (next: string) => {
      if (!isControlled) {
        setUncontrolledValue(next)
      }
      onChange?.(next)
    },
    [isControlled, onChange]
  )

  // Pre-compute item order at the root. Items are direct children whose
  // component type === GovukRadiosItem. The first item gets the bare `${name}`
  // as its id, subsequent items get `${name}-2`, `${name}-3`, … matching the
  // canonical GDS reference markup.
  const orderedValues = useMemo(() => {
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
  }, [children])

  const getItemIndex = useCallback(
    (itemValue: string) => {
      const idx = orderedValues.indexOf(itemValue)
      return idx === -1 ? 0 : idx
    },
    [orderedValues]
  )

  const contextValue = useMemo<RadiosContextValue>(
    () => ({
      name,
      selectedValue,
      disabled: Boolean(disabled),
      setValue,
      getItemIndex,
    }),
    [name, selectedValue, disabled, setValue, getItemIndex]
  )

  return (
    <RadiosContext.Provider value={contextValue}>
      <div
        {...rest}
        ref={ref}
        className={cn('govuk-radios', className)}
      >
        {children}
      </div>
    </RadiosContext.Provider>
  )
})

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
  const resolvedId =
    id ?? (index === 0 ? ctx.name : `${ctx.name}-${index + 1}`)
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
      <label
        className="govuk-label govuk-radios__label"
        htmlFor={resolvedId}
      >
        {children}
      </label>
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
