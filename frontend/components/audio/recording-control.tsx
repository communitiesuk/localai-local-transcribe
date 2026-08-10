'use client'

import { GovukButton, GovukButtonGroup } from '@/components/govuk'
import React, { useEffect, useRef, useState } from 'react'
import { useRecordingUiStore } from '@/stores/use-recording-ui-store'

interface RecordingControlProps {
  stream: MediaStream | null
  isRecording: boolean
  onStopRecording: () => void
  recorderControls?: {
    togglePauseResume?: () => void
    isPaused?: boolean
  }
  onPauseStateChange?: (isPaused: boolean) => void
}

export default function RecordingControl({
  stream,
  isRecording,
  onStopRecording,
  recorderControls,
  onPauseStateChange,
}: RecordingControlProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const [showStopConfirm, setShowStopConfirm] = useState(false)
  const [localIsPaused, setLocalIsPaused] = useState(false)
  const [recordingDurationSeconds, setRecordingDurationSeconds] = useState(0)
  const recordingStartedAtRef = useRef<number | null>(null)
  const accumulatedRecordingMsRef = useRef(0)

  const setRecordingState = useRecordingUiStore(
    (state) => state.setRecordingState
  )

  const mediaTracks = stream ? stream.getAudioTracks() : []
  const isPaused =
    recorderControls?.isPaused !== undefined
      ? recorderControls.isPaused
      : localIsPaused

  useEffect(() => {
    if (!isRecording) {
      setRecordingState('idle')
      return
    }

    setRecordingState(isPaused ? 'paused' : 'recording')
  }, [isRecording, isPaused, setRecordingState])

  useEffect(() => {
    if (!isRecording) {
      recordingStartedAtRef.current = null
      accumulatedRecordingMsRef.current = 0
      setRecordingDurationSeconds(0)
      return
    }

    if (isPaused && recordingStartedAtRef.current !== null) {
      accumulatedRecordingMsRef.current +=
        Date.now() - recordingStartedAtRef.current
      recordingStartedAtRef.current = null
      return
    }

    if (recordingStartedAtRef.current === null) {
      recordingStartedAtRef.current = Date.now()
    }

    const updateDuration = () => {
      const currentSessionMs =
        recordingStartedAtRef.current === null
          ? 0
          : Date.now() - recordingStartedAtRef.current

      setRecordingDurationSeconds(
        Math.floor(
          (accumulatedRecordingMsRef.current + currentSessionMs) / 1000
        )
      )
    }

    updateDuration()

    const interval = window.setInterval(updateDuration, 1000)

    return () => {
      window.clearInterval(interval)
    }
  }, [isRecording, isPaused])

  const formattedRecordingDuration = new Date(recordingDurationSeconds * 1000)
    .toISOString()
    .substring(11, 19)

  useEffect(() => {
    const isValidStream =
      stream && stream.active && stream.getAudioTracks().length > 0

    if (!isValidStream || !isRecording) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(console.error)
        audioContextRef.current = null
      }
      analyserRef.current = null
      dataArrayRef.current = null

      const canvas = canvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)

          if (canvas.width > 0 && canvas.height > 0) {
            ctx.fillStyle = '#666'
            ctx.font = '14px sans-serif'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'
            ctx.fillText(
              'Waiting for audio...',
              canvas.width / 2,
              canvas.height / 2
            )
          }
        }
      }
      return
    }

    try {
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(console.error)
        audioContextRef.current = null
        analyserRef.current = null
      }

      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      analyserRef.current.smoothingTimeConstant = 0.7

      const bufferLength = analyserRef.current.frequencyBinCount
      dataArrayRef.current = new Uint8Array(bufferLength)

      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
    } catch (error) {
      console.error('Error setting up audio context', error)
    }

    const draw = () => {
      try {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        const { width, height } = canvas
        if (width === 0 || height === 0) return

        if (!isRecording || !analyserRef.current || !dataArrayRef.current) {
          ctx.clearRect(0, 0, width, height)

          const time = Date.now() / 1000
          const pulseSize = Math.sin(time * 2) * 0.1 + 0.9

          ctx.fillStyle = '#3b82f6'
          ctx.beginPath()
          ctx.arc(
            width / 2,
            height / 2,
            (Math.min(width, height) / 10) * pulseSize,
            0,
            Math.PI * 2
          )
          ctx.fill()

          ctx.fillStyle = '#fff'
          ctx.font = '14px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText('Waiting for audio...', width / 2, height / 2)

          animationRef.current = requestAnimationFrame(draw)
          return
        }

        const analyser = analyserRef.current
        const dataArray = dataArrayRef.current

        ctx.clearRect(0, 0, width, height)

        analyser.getByteFrequencyData(dataArray)

        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        const hasAudioData = average > 5

        if (!hasAudioData || isPaused) {
          const time = Date.now() / 1000
          const pulseSize = Math.sin(time * 2) * 0.1 + 0.9

          ctx.fillStyle = isPaused ? '#6b7280' : '#3b82f6'
          ctx.beginPath()
          ctx.arc(
            width / 2,
            height / 2,
            (Math.min(width, height) / 10) * pulseSize,
            0,
            Math.PI * 2
          )
          ctx.fill()
        } else {
          const barCount = Math.min(dataArray.length / 2, 64)
          const barWidth = (width / barCount) * 0.8
          const barSpacing = 2
          const totalBarWidth = barCount * (barWidth + barSpacing)
          const startX = (width - totalBarWidth) / 2

          for (let i = 0; i < barCount; i += 1) {
            const value = dataArray[i]
            const multiplier = 1.2
            const barHeight = Math.min(
              (value / 255) * height * multiplier * 0.8,
              height * 0.8
            )

            const x = startX + i * (barWidth + barSpacing)
            const gradient = ctx.createLinearGradient(
              0,
              (height - barHeight) / 2,
              0,
              (height + barHeight) / 2
            )
            const hue = 210 + (i / barCount) * 30
            gradient.addColorStop(0, `hsla(${hue}, 100%, 70%, 0.9)`)
            gradient.addColorStop(1, `hsla(${hue}, 100%, 50%, 0.7)`)
            ctx.fillStyle = gradient

            const y = (height - barHeight) / 2
            const radius = Math.min(barWidth / 2, 4)

            ctx.beginPath()
            ctx.moveTo(x + radius, y)
            ctx.lineTo(x + barWidth - radius, y)
            ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius)
            ctx.lineTo(x + barWidth, y + barHeight - radius)
            ctx.quadraticCurveTo(
              x + barWidth,
              y + barHeight,
              x + barWidth - radius,
              y + barHeight
            )
            ctx.lineTo(x + radius, y + barHeight)
            ctx.quadraticCurveTo(x, y + barHeight, x, y + barHeight - radius)
            ctx.lineTo(x, y + radius)
            ctx.quadraticCurveTo(x, y, x + radius, y)
            ctx.fill()
          }

          if (average > 20) {
            const centerX = width / 2
            const centerY = height / 2
            const maxRadius = Math.min(width, height) / 6
            const radius = (average / 255) * maxRadius

            const circleGradient = ctx.createRadialGradient(
              centerX,
              centerY,
              0,
              centerX,
              centerY,
              radius
            )
            circleGradient.addColorStop(0, 'rgba(255, 255, 255, 0.4)')
            circleGradient.addColorStop(0.7, 'rgba(59, 130, 246, 0.2)')
            circleGradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

            ctx.fillStyle = circleGradient
            ctx.beginPath()
            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
            ctx.fill()
          }
        }
      } catch (error) {
        console.error('Error in draw function:', error)
      }

      animationRef.current = requestAnimationFrame(draw)
    }

    const resizeCanvas = () => {
      if (canvasRef.current) {
        const canvas = canvasRef.current
        const container = canvas.parentElement
        if (container) {
          const { width, height } = container.getBoundingClientRect()
          canvas.width = width
          canvas.height = height
        }
      }
    }

    resizeCanvas()
    const resizeObserver = new ResizeObserver(resizeCanvas)
    if (canvasRef.current?.parentElement) {
      resizeObserver.observe(canvasRef.current.parentElement)
    }
    window.addEventListener('resize', resizeCanvas)

    draw()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      resizeObserver.disconnect()
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [stream, isRecording, isPaused])

  const togglePause = () => {
    if (recorderControls?.togglePauseResume) {
      recorderControls.togglePauseResume()
    } else if (stream && mediaTracks.length > 0) {
      const newPausedState = !isPaused
      mediaTracks.forEach((track) => {
        const newTrack = track
        newTrack.enabled = !newPausedState
      })
      setLocalIsPaused(newPausedState)
      if (onPauseStateChange) {
        onPauseStateChange(newPausedState)
      }
    }
  }

  const handleStopRecording = () => {
    setShowStopConfirm(true)
  }

  const confirmStop = () => {
    onStopRecording()
    setShowStopConfirm(false)
  }

  return (
    <div className="space-y-4">
      <p>Recording length: {formattedRecordingDuration}</p>

      <div
        ref={containerRef}
        className="relative h-20 w-full overflow-hidden rounded-md border-2 border-blue-200 bg-transparent dark:border-blue-800"
      >
        <canvas ref={canvasRef} className="size-full" />
        {!isRecording && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            Audio visualization will appear here when recording
          </div>
        )}
        {isRecording && !stream && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100/80 text-sm text-gray-500 dark:bg-gray-800/80 dark:text-gray-400">
            Connecting to audio stream...
          </div>
        )}
      </div>
      {isRecording && !showStopConfirm && (
        <GovukButtonGroup>
          <GovukButton
            type="button"
            onClick={togglePause}
            variant="secondary"
            className="min-w-36"
          >
            {isPaused ? 'Resume' : 'Pause'}
          </GovukButton>
          <GovukButton
            type="button"
            onClick={handleStopRecording}
            variant="warning"
            className="min-w-36"
          >
            Stop
          </GovukButton>
        </GovukButtonGroup>
      )}
      {showStopConfirm && (
        <div className="govuk-inset-text">
          <p className="govuk-body">
            Are you sure you want to stop recording? You won&apos;t be able to
            resume recording after stopping.
          </p>
          <div className="flex gap-2">
            <GovukButton type="button" onClick={confirmStop} variant="warning">
              Stop Recording
            </GovukButton>
            <GovukButton
              type="button"
              onClick={() => setShowStopConfirm(false)}
              variant="secondary"
            >
              Cancel
            </GovukButton>
          </div>
        </div>
      )}
    </div>
  )
}
