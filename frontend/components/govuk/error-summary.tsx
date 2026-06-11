import { cn } from '@/lib/utils'

export type ErrorItem = { href?: string; text: string }

type Props = {
  title?: string
  description?: string
  className?: string
  errorList: ErrorItem[]
} & Omit<
  React.HTMLAttributes<HTMLDivElement>,
  'className' | 'children' | 'role'
>

export function GovukErrorSummary({
  title = 'There is a problem',
  description,
  className,
  errorList,
  ...rest
}: Props) {
  return (
    <div
      {...rest}
      className={cn('govuk-error-summary', className)}
      data-module="govuk-error-summary"
    >
      <div role="alert">
        <h2 className="govuk-error-summary__title">{title}</h2>
        <div className="govuk-error-summary__body">
          {description && <p>{description}</p>}
          <ul className="govuk-list govuk-error-summary__list">
            {errorList.map((item) => (
              <li key={item.text}>
                {item.href ? <a href={item.href}>{item.text}</a> : item.text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
