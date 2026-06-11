'use client'

import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'warning' | 'inverse'

type CommonProps = {
  variant?: Variant
  isStartButton?: boolean
  className?: string
  children: React.ReactNode
}

type ButtonProps = CommonProps &
  Omit<
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    'className' | 'children' | 'disabled' | 'type'
  > & {
    disabled?: boolean
    type?: 'submit' | 'button' | 'reset'
  }

type ButtonLinkProps = CommonProps &
  Omit<
    React.AnchorHTMLAttributes<HTMLAnchorElement>,
    'className' | 'children' | 'role' | 'draggable'
  > & {
    href: string
  }

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

function useButtonClasses(variant: Variant, isStartButton?: boolean, className?: string) {
  const variantClass: Record<Variant, string | undefined> = {
    primary: undefined,
    secondary: 'govuk-button--secondary',
    warning: 'govuk-button--warning',
    inverse: 'govuk-button--inverse',
  }
  return cn('govuk-button', variantClass[variant], isStartButton && 'govuk-button--start', className)
}

export function GovukButton({
  variant = 'primary',
  isStartButton,
  className,
  children,
  disabled,
  type,
  ...rest
}: ButtonProps) {
  const classes = useButtonClasses(variant, isStartButton, className)
  const isDisabled = Boolean(disabled)

  return (
    <button
      {...rest}
      type={type ?? 'submit'}
      disabled={isDisabled}
      className={classes}
      data-module="govuk-button"
    >
      {children}
      {isStartButton && <StartIcon />}
    </button>
  )
}

export function GovukButtonLink({
  variant = 'primary',
  isStartButton,
  className,
  children,
  ...rest
}: ButtonLinkProps) {
  const classes = useButtonClasses(variant, isStartButton, className)

  return (
    <a
      {...rest}
      role="button"
      draggable={false}
      className={classes}
      data-module="govuk-button"
    >
      {children}
      {isStartButton && <StartIcon />}
    </a>
  )
}
