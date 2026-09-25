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
}

export function GovukBackLinkWithLockNav({
  href,
  message,
}: GovBackLinkWithLockNavProps) {
  const router = useRouter()
  const { lockNavigation, setLockNavigation } = useLockNavigationContext()

  if (!lockNavigation) {
    return <GovukBackLink href={href} />
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <a className="govuk-back-link" role="button" tabIndex={0}>
          Back
        </a>
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
