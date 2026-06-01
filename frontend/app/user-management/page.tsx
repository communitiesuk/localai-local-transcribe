'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useUsers } from '@/hooks/use-users'

export default function SupportPage() {
  const organisation_id = 'placeholder'
  const { users } = useUsers(organisation_id)

  const router = useRouter()
  return (
    <div className="mx-auto max-w-3xl pt-1">
      <Button
        variant="link"
        className="mb-4 self-start px-0! underline hover:decoration-2"
        onClick={() => {
          router.back()
        }}
      >
        <span className="flex items-center">
          <ChevronLeft />
          Back
        </span>
      </Button>
      <h1 className="text-3xl font-bold">User Management</h1>
      <div className="text-muted-foreground">
        Manage users in your organisation
      </div>

      {users && (
        <ul>
          {users.map((user) => (
            <li key={user.id}>{user.email}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
