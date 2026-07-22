'use client'

import { GovukButton } from '@/components/govuk'
import { DeleteDialog } from '@/components/recent-meetings/delete-transcription-dialog'
import { RenameDialog } from '@/components/recent-meetings/rename-dialog'
import { TranscriptionCard } from '@/components/recent-meetings/transcription-card'
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
    <li className="justify-between rounded-md border border-[var(--govuk-border-colour)] p-3 transition-colors hover:bg-[var(--govuk-surface-background-colour)] sm:flex">
      <Link href={`/transcriptions/${transcription.id}`}>
        <TranscriptionCard transcription={transcription} />
      </Link>
      <div className="govuk-!-margin-top-2 flex items-start gap-2">
        <GovukButton
          type="button"
          variant="secondary"
          className="govuk-!-margin-bottom-0"
          onClick={() => setRenameOpen(true)}
        >
          Rename
        </GovukButton>
        <GovukButton
          type="button"
          variant="warning"
          className="govuk-!-margin-bottom-0"
          onClick={() => setDeleteOpen(true)}
        >
          Delete
        </GovukButton>
      </div>
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
