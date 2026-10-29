'use client'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { GovukBackLink } from '@/components/govuk'
import { useLockNavigationContext } from '@/hooks/use-lock-navigation-context'
import { useRouter } from 'next/navigation'

type GovBackLinkWithLockNavProps = {
  href: string
  message: string
  onLeave?: () => void
}

export function GovukBackLinkWithLockNav({
  href,
  message,
  onLeave,
}: GovBackLinkWithLockNavProps) {
  const router = useRouter()
  const { lockNavigation, setLockNavigation } = useLockNavigationContext()

  if (!lockNavigation) {
    return <GovukBackLink href={href} />
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <button
          type="button"
          className="govuk-back-link"
          style={{
            background: 'none',
            border: 'none',
            padding: 0,
            font: 'inherit',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          Back
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Are you sure you want to leave the page?
          </AlertDialogTitle>
          <AlertDialogDescription>{message}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              onLeave?.()
              setLockNavigation(false)
              router.push(href)
            }}
          >
            Continue
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
