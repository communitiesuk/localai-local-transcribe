import { GovukButton, GovukButtonGroup } from '@/components/govuk'

interface ModalConfirmationInterstitialProps {
  title: string
  body: React.ReactNode
  confirmLabel: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
  isWarning?: boolean
}

export function ModalConfirmationInterstitial({
  title,
  body,
  confirmLabel,
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  isWarning = false,
}: ModalConfirmationInterstitialProps) {
  return (
    <div>
      <h2 className="govuk-heading-l">{title}</h2>
      {isWarning ? (
        <div className="govuk-warning-text">
          <span className="govuk-warning-text__icon" aria-hidden="true">
            !
          </span>
          <strong className="govuk-warning-text__text">
            <span className="govuk-visually-hidden">Warning</span>
            {body}
          </strong>
        </div>
      ) : (
        body
      )}
      <GovukButtonGroup className="govuk-!-margin-top-4">
        <GovukButton type="button" variant="warning" onClick={onConfirm}>
          {confirmLabel}
        </GovukButton>
        <GovukButton type="button" variant="link" onClick={onCancel}>
          {cancelLabel}
        </GovukButton>
      </GovukButtonGroup>
    </div>
  )
}
