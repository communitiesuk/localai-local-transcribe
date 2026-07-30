'use client'

import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { ChangeEvent } from 'react'

export const RecordingsSort = () => {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  const sort = searchParams.get('sort') === 'oldest' ? 'oldest' : 'newest'

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const params = new URLSearchParams(searchParams)
    params.set('sort', event.target.value)
    params.delete('page')
    router.replace(`${pathname}?${params.toString()}`)
  }

  return (
    <div className="govuk-form-group">
      <label className="govuk-label" htmlFor="sort-recordings">
        Sort by
      </label>
      <select
        className="govuk-select"
        id="sort-recordings"
        name="sort-recordings"
        value={sort}
        onChange={handleChange}
      >
        <option value="newest">Date recorded (newest to oldest)</option>
        <option value="oldest">Date recorded (oldest to newest)</option>
      </select>
    </div>
  )
}
