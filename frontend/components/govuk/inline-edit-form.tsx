'use client'

import { GovukButton, GovukInput } from '@/components/govuk'
import { useState, useId } from 'react'

interface InlineEditFormProps {
  name: string
  onUpdate: (newName: string) => void
  onCancel: () => void
}

export function InLineEditForm({
  name,
  onUpdate,
  onCancel,
}: InlineEditFormProps) {
  const [value, setValue] = useState(name)
  const [initialValue] = useState(name)
  const id = useId()

  return (
    <>
      <GovukInput
        id={id}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label={`Edit ${name}`}
      />
      <div className="govuk-button-group govuk-!-margin-top-3">
        <GovukButton
          type="button"
          onClick={() => onUpdate(value)}
          disabled={value === initialValue || !value?.trim()}
        >
          Update
        </GovukButton>
        <GovukButton type="button" variant="link" onClick={() => onCancel()}>
          Cancel
        </GovukButton>
      </div>
    </>
  )
}
