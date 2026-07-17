'use client'

import { DeleteDialog } from '@/components/recent-meetings/delete-transcription-dialog'
import { RenameDialog } from '@/components/recent-meetings/rename-dialog'
import { TranscriptionCard } from '@/components/recent-meetings/transcription-card'
import { GovukButton } from '@/components/govuk'
import { TranscriptionMetadata } from '@/lib/client'
import Link from 'next/link'
import { useState } from 'react'

export const TranscriptionListItem = ({
  transcription,
}: {
  transcription: TranscriptionMetadata
}) => {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [renameOpen, setRenameOpen] = useState(false)
  return (
    <li>
      <Link
        href={`/transcriptions/${transcription.id}`}
        className="justify-between rounded-md border border-[var(--govuk-border-colour)] p-3 transition-colors hover:bg-[var(--govuk-surface-background-colour)] sm:flex"
      >
        <TranscriptionCard transcription={transcription} />
        <div className="govuk-!-margin-top-2 flex items-start gap-2">
          <GovukButton
            type="button"
            variant="secondary"
            className="govuk-!-margin-bottom-0"
            onClick={(e) => {
              e.preventDefault()
              setRenameOpen(true)
            }}
          >
            Rename
          </GovukButton>
          <GovukButton
            type="button"
            variant="warning"
            className="govuk-!-margin-bottom-0"
            onClick={(e) => {
              e.preventDefault()
              setDeleteOpen(true)
            }}
          >
            Delete
          </GovukButton>
        </div>
      </Link>
      <DeleteDialog
        open={deleteOpen}
        setOpen={setDeleteOpen}
        transcription={transcription}
      />
      <RenameDialog
        open={renameOpen}
        setOpen={setRenameOpen}
        transcription={transcription}
      />
    </li>
  )
}
