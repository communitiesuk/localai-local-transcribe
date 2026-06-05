import { cn } from '@/lib/utils'

export type ErrorItem = { href?: string; text: string }

type CommonProps = {
  title?: string
  description?: string
  className?: string
} & Omit<
  React.HTMLAttributes<HTMLDivElement>,
  'className' | 'children' | 'role'
>

type ListProps = CommonProps & {
  errorList: ErrorItem[]
  errors?: never
}

type RhfErrors = Record<string, { message?: string } | undefined>

type RhfProps = CommonProps & {
  errorList?: never
  errors: RhfErrors
}

type Props = ListProps | RhfProps

function normaliseErrors(
  errorList: ErrorItem[] | undefined,
  errors: RhfErrors | undefined
): ErrorItem[] {
  if (errorList) return errorList
  if (errors) {
    return Object.entries(errors).map(([name, fieldError]) => ({
      text: fieldError?.message ?? name,
    }))
  }
  return []
}

export function GovukErrorSummary(props: Props) {
  const {
    title = 'There is a problem',
    description,
    className,
    errorList,
    errors,
    ...spreadable
  } = props as CommonProps & {
    errorList?: ErrorItem[]
    errors?: RhfErrors
  }
  const items = normaliseErrors(errorList, errors)

  return (
    <div
      {...spreadable}
      className={cn('govuk-error-summary', className)}
      data-module="govuk-error-summary"
    >
      <div role="alert">
        <h2 className="govuk-error-summary__title">{title}</h2>
        <div className="govuk-error-summary__body">
          {description && <p>{description}</p>}
          <ul className="govuk-list govuk-error-summary__list">
            {items.map((item, index) => (
              <li key={`${item.text}-${index}`}>
                {item.href ? <a href={item.href}>{item.text}</a> : item.text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
