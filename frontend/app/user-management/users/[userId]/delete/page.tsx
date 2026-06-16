import { use } from 'react'

export default function UserPage(props: {
  params: Promise<{ userId: string }>
}) {
  const { userId } = use(props.params)
  return (
    <>
      <p>heading</p>
      {userId}
    </>
  )
}
