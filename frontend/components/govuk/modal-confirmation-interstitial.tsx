import { GovukButton, GovukButtonGroup } from '@/components/govuk'

interface ModalConfirmationInterstitialProps {
  title: string
  body: string
  confirmLabel: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ModalConfirmationInterstitial({
  title,
  body,
  confirmLabel,
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}: ModalConfirmationInterstitialProps) {
  return (
    <div>
      <h2 className="govuk-heading-l">{title}</h2>
      <p className="govuk-body">{body}</p>
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
