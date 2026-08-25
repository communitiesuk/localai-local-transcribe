'use client'

import { GovukButton, GovukInput } from '@/components/govuk'
import { useState, useId } from 'react'

interface InlineEditFormProps {
  name: string
  onUpdate: (newName: string) => void
  onCancel: () => void
  value?: string
  onValueChange?: (value: string) => void
  updateLabel?: string
  secondaryUpdate?: {
    label: string
    onUpdate: (newName: string) => void
  }
  disabled?: boolean
}

export function InLineEditForm({
  name,
  onUpdate,
  onCancel,
  value: controlledValue,
  onValueChange,
  updateLabel = 'Update all occurrences',
  secondaryUpdate,
  disabled = false,
}: InlineEditFormProps) {
  const [internalValue, setInternalValue] = useState(name)
  const [initialValue] = useState(name)
  const id = useId()
  const value = controlledValue ?? internalValue

  const handleValueChange = (value: string) => {
    if (controlledValue === undefined) {
      setInternalValue(value)
    }
    onValueChange?.(value)
  }

  return (
    <>
      <GovukInput
        id={id}
        value={value}
        onChange={(e) => handleValueChange(e.target.value)}
        aria-label={`Edit ${name}`}
      />
      <div className="govuk-button-group govuk-!-margin-top-3">
        <GovukButton
          type="button"
          onClick={() => onUpdate(value)}
          disabled={disabled || value === initialValue || !value?.trim()}
        >
          {updateLabel}
        </GovukButton>
        {secondaryUpdate && (
          <GovukButton
            type="button"
            variant="secondary"
            onClick={() => secondaryUpdate.onUpdate(value)}
            disabled={disabled || value === initialValue || !value?.trim()}
          >
            {secondaryUpdate.label}
          </GovukButton>
        )}
        <GovukButton type="button" variant="link" onClick={() => onCancel()}>
          Cancel
        </GovukButton>
      </div>
    </>
  )
}
