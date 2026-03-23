'use client'

import { client } from '@/lib/client/client.gen'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { API_PROXY_PATH } from '@/lib/constants'
const queryClient = new QueryClient()

client.setConfig({ baseUrl: API_PROXY_PATH })

export const TanstackQueryProvider = ({
  children,
}: {
  children: ReactNode
}) => {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
