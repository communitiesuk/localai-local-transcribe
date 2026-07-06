import { Suspense } from 'react'
import UserManagementClient from '@/components/user-management/client-page'

export default function UserManagementPage() {
  return (
    <Suspense fallback={null}>
      <UserManagementClient />
    </Suspense>
  )
}
