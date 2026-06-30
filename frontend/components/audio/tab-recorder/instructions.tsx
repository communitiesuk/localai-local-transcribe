'use client'

import Image from 'next/image'
import { useState } from 'react'

const TABS = [
  { id: 'windows', label: 'Windows' },
  { id: 'macos', label: 'macOS' },
]

export const InstructionsTabs = () => {
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof navigator === 'undefined') return 'windows'
    const platform =
      (navigator as Navigator & { userAgentData?: { platform: string } })
        .userAgentData?.platform || navigator.platform
    return platform.toLowerCase().includes('mac') ? 'macos' : 'windows'
  })

  return (
    <div className="govuk-tabs">
      <ul className="govuk-tabs__list" role="tablist">
        {TABS.map((tab) => (
          <li
            key={tab.id}
            className={`govuk-tabs__list-item${activeTab === tab.id ? 'govuk-tabs__list-item--selected' : ''}`}
            role="presentation"
          >
            <a
              className="govuk-tabs__tab"
              href={`#${tab.id}`}
              id={`tab_${tab.id}`}
              role="tab"
              aria-controls={tab.id}
              aria-selected={activeTab === tab.id}
              tabIndex={activeTab === tab.id ? 0 : -1}
              onClick={(e) => {
                e.preventDefault()
                setActiveTab(tab.id)
              }}
            >
              {tab.id === 'windows' ? (
                <span className="flex items-center gap-1">
                  <svg
                    className="inline size-4"
                    viewBox="0 0 22 22"
                    aria-hidden="true"
                  >
                    <g fill="#000000">
                      <rect width="10" height="10" x="0" y="0" />
                      <rect width="10" height="10" x="11" y="0" />
                      <rect width="10" height="10" x="0" y="11" />
                      <rect width="10" height="10" x="11" y="11" />
                    </g>
                  </svg>
                  Windows
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <Image
                    src="/apple.svg"
                    width={12}
                    height={12}
                    className="inline"
                    alt=""
                    aria-hidden="true"
                  />
                  macOS
                </span>
              )}
            </a>
          </li>
        ))}
      </ul>

      <div
        className={`govuk-tabs__panel${activeTab !== 'windows' ? 'govuk-tabs__panel--hidden' : ''}`}
        id="windows"
        role="tabpanel"
        aria-labelledby="tab_windows"
      >
        <ol className="govuk-list govuk-list--number flex flex-col gap-2">
          <li>
            <p className="govuk-body">
              <strong>Choose your microphone</strong> - This microphone will
              record you and those in the room with you. Note that it will
              continue recording regardless of whether you are muted in the
              virtual meeting.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Join your meeting</strong> - Join your meeting in Teams,
              Google Meet, Zoom.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Share your screen</strong> - When prompted, click the
              &quot;<strong>Entire Screen</strong>&quot; tab and select the
              screen where the meeting is showing.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Select &quot;Share Audio&quot;</strong>. Switch on the
              &quot;Share Audio&quot; the toggle in the bottom right of the
              share window.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Keep Minute open</strong> - It doesn&apos;t need to be
              visible on screen, but do not close Minute&apos;s tab
            </p>
          </li>
        </ol>
      </div>

      <div
        className={`govuk-tabs__panel${activeTab !== 'macos' ? 'govuk-tabs__panel--hidden' : ''}`}
        id="macos"
        role="tabpanel"
        aria-labelledby="tab_macos"
      >
        <ol className="govuk-list govuk-list--number flex flex-col gap-2">
          <li>
            <p className="govuk-body">
              <strong>Choose your microphone</strong> - This microphone will
              record you and those in the room with you. Note that it will
              continue recording regardless of whether you are muted in the
              virtual meeting.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Join your meeting</strong> - Join your meeting in a
              browser tab. It must be the same browser that Minute is running
              in. Do not use a desktop app. Desktop apps cannot be recorded.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Share the right tab</strong> - When prompted, select the
              tab where you have joined the meeting.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Select &quot;Share Audio&quot;</strong>. Switch on the
              &quot;Share Audio&quot; the toggle in the bottom right of the
              share window.
            </p>
          </li>
          <li>
            <p className="govuk-body">
              <strong>Keep both tabs open</strong> - Don&apos;t close either tab
              during recording. Switching between tabs is fine, but both must
              remain open.
            </p>
          </li>
        </ol>
      </div>
    </div>
  )
}
