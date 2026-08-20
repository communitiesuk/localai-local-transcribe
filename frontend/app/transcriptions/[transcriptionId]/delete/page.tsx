'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  deleteTranscriptionTranscriptionsTranscriptionIdDeleteMutation,
  listLabelledTranscriptionsTranscriptionsLabelledGetQueryKey,
  listUnlabelledTranscriptionsTranscriptionsUnlabelledGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { GovukWarningText } from '@/components/govuk'

export default function DeleteTranscriptionPage(props: {
  params: Promise<{ transcriptionId: string }>
}) {
  const { transcriptionId } = use(props.params)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()

  const { mutate, isPending } = useMutation({
    ...deleteTranscriptionTranscriptionsTranscriptionIdDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey:
          listUnlabelledTranscriptionsTranscriptionsUnlabelledGetQueryKey(),
      })
      queryClient.invalidateQueries({
        queryKey: listLabelledTranscriptionsTranscriptionsLabelledGetQueryKey(),
      })
      setBanner({
        variant: 'important',
        title: 'Recording deleted',
        message: 'Your recording has been deleted',
      })
      // TODO AIILG-497: add event for deleting transcription
    },
  })

  return (
    <ConfirmationInterstitial
      title={'Are you sure you want to delete this recording?'}
      actionLabel={'Delete'}
      actionVariant={'warning'}
      onAction={() =>
        mutate({
          path: {
            transcription_id: transcriptionId,
          },
        })
      }
      actionPending={isPending}
      cancelHref={`/transcriptions/${transcriptionId}`}
    >
      <GovukWarningText>
        If you proceed, you will not be able to recover this recording.
      </GovukWarningText>
    </ConfirmationInterstitial>
  )
}
