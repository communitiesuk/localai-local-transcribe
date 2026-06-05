'use client'

import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'warning' | 'inverse'

type CommonProps = {
  variant?: Variant
  isStartButton?: boolean
  isSubmitting?: boolean
  loadingText?: string
  preventDoubleClick?: boolean
  className?: string
  children: React.ReactNode
}

type ButtonOnly = {
  href?: never
} & Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  'className' | 'children' | 'disabled' | 'type'
> & {
    disabled?: boolean
    type?: 'submit' | 'button' | 'reset'
  }

type AnchorOnly = {
  href: string
} & Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'className' | 'children' | 'href' | 'role' | 'draggable'
>

type Props = CommonProps & (ButtonOnly | AnchorOnly)

function StartIcon() {
  return (
    <svg
      className="govuk-button__start-icon"
      xmlns="http://www.w3.org/2000/svg"
      width="17.5"
      height="19"
      viewBox="0 0 33 40"
      aria-hidden="true"
      focusable="false"
    >
      <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
    </svg>
  )
}

export function GovukButton(props: Props) {
  const {
    variant = 'primary',
    isStartButton,
    isSubmitting,
    loadingText = 'Saving…',
    preventDoubleClick,
    className,
    children,
    ...rest
  } = props

  const variantClass: Record<Variant, string | undefined> = {
    primary: undefined,
    secondary: 'govuk-button--secondary',
    warning: 'govuk-button--warning',
    inverse: 'govuk-button--inverse',
  }

  const classes = cn(
    'govuk-button',
    variantClass[variant],
    isStartButton && 'govuk-button--start',
    className
  )

  const content = (
    <>
      {isSubmitting ? loadingText : children}
      {isStartButton && <StartIcon />}
    </>
  )

  if ('href' in rest && rest.href !== undefined) {
    const { href, ...anchorRest } = rest as { href: string } & Record<
      string,
      unknown
    >
    return (
      <a
        {...anchorRest}
        href={href as string}
        role="button"
        draggable={false}
        className={classes}
        data-module="govuk-button"
      >
        {content}
      </a>
    )
  }

  const {
    disabled: callerDisabled,
    type,
    ...buttonRest
  } = rest as {
    disabled?: boolean
    type?: 'submit' | 'button' | 'reset'
  } & Record<string, unknown>

  const isDisabled = Boolean(isSubmitting || callerDisabled)

  return (
    <button
      {...buttonRest}
      type={type ?? 'submit'}
      disabled={isDisabled}
      aria-disabled={isDisabled || undefined}
      className={classes}
      data-module="govuk-button"
      data-prevent-double-click={
        preventDoubleClick ? 'true' : undefined
      }
    >
      {content}
    </button>
  )
}
