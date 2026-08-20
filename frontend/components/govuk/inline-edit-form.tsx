'use client'

import { GovukButton, GovukInput } from '@/components/govuk'
import { useState, useId } from 'react'

interface InlineEditFormProps {
  name: string
  defaultValue?: string
  onUpdate: (newName: string) => void
  onCancel: (currentValue: string) => void
}

export function InLineEditForm({
  name,
  defaultValue,
  onUpdate,
  onCancel,
}: InlineEditFormProps) {
  const [value, setValue] = useState(defaultValue ?? name)
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
          disabled={value === initialValue}
        >
          Update
        </GovukButton>
        <GovukButton
          type="button"
          variant="link"
          onClick={() => onCancel(value)}
        >
          Cancel
        </GovukButton>
      </div>
    </>
  )
}
