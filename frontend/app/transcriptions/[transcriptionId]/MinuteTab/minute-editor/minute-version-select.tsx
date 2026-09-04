'use client'

import { ContentSource, MinuteVersionResponse } from '@/lib/client'
import { Dispatch, SetStateAction } from 'react'
import { GovukLabel, GovukSelect } from '@/components/govuk'

const formatVersionDate = (date: string): string => {
  const parsedDate = new Date(date)
  return `${parsedDate.toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: '2-digit' })} ${parsedDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
}

const MapContentSource = (source: ContentSource): string => {
  switch (source) {
    case 'ai_edit':
      return 'AI edit'
    case 'manual_edit':
      return 'Manual edit'
    case 'initial_generation':
      return 'Original'
  }
}

export const MinuteVersionSelect = ({
  minuteVersions,
  version,
  setVersion,
  disabled,
}: {
  minuteVersions: MinuteVersionResponse[]
  version?: string
  setVersion: Dispatch<SetStateAction<string | undefined>>
  disabled?: boolean
}) => {
  return (
    <div>
      <GovukLabel className="govuk-!-margin-bottom-2" htmlFor="version-select">
        Version history
      </GovukLabel>
      <GovukSelect
        id="version-select"
        name="version-select"
        value={version}
        onChange={(e) => setVersion(e.target.value)}
        disabled={disabled}
      >
        {minuteVersions.map((v, i) => {
          return (
            <option key={v.id} value={v.id}>
              {minuteVersions.length - i}. {MapContentSource(v.content_source)}{' '}
              ({formatVersionDate(v.created_datetime)})
            </option>
          )
        })}
      </GovukSelect>
    </div>
  )
}
