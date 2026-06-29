import { getFileExtensionFromBlob } from '@/lib/getFileExtension'
import { Pause, Play } from 'lucide-react'
import { ChangeEventHandler, useEffect, useMemo, useRef, useState } from 'react'

export default function AudioPlayerComponent({
  audioBlob,
}: {
  audioBlob: Blob
}) {
  const ref = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setPlaying] = useState(false)
  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState<number>()

  const audioUrl = useMemo(() => URL.createObjectURL(audioBlob), [audioBlob])
  const filename = useMemo(
    () => `audio-file.${getFileExtensionFromBlob(audioBlob)}`,
    [audioBlob]
  )

  useEffect(() => {
    return () => URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  useEffect(() => {
    const src = URL.createObjectURL(audioBlob)
    if (!ref.current) {
      ref.current = new Audio()
    }
    ref.current.src = src
    ref.current.preload = 'metadata'
    const audio = ref.current

    const onLoadedMetadata = () => {
      if (audio.duration === Infinity || isNaN(Number(audio.duration))) {
        getDuration(audioBlob).then((duration) => setDuration(duration))
      } else {
        setDuration(audio.duration)
      }
    }
    const onPlay = () => {
      setPlaying(true)
    }
    const onPause = () => {
      setPlaying(false)
    }
    const onTimeUpdate = () => {
      setTime(audio.currentTime)
    }
    const onEnded = () => {
      audio.currentTime = 0
    }

    audio.addEventListener('loadedmetadata', onLoadedMetadata)
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('timeupdate', onTimeUpdate)
    audio.addEventListener('ended', onEnded)
    return () => {
      audio.pause()
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('timeupdate', onTimeUpdate)
      audio.removeEventListener('onloadedmetadata', onLoadedMetadata)
      audio.removeEventListener('ended', onEnded)
      URL.revokeObjectURL(src)
    }
  }, [audioBlob])

  const togglePlayPause = () => {
    if (ref.current) {
      if (ref.current.paused) {
        ref.current.play()
      } else {
        ref.current.pause()
      }
    }
  }

  const handleSeek: ChangeEventHandler<HTMLInputElement> = (e) => {
    const target = e.target as HTMLInputElement
    const seekTime = parseFloat(target.value)
    if (ref.current) {
      ref.current.currentTime = seekTime
    }
  }

  return (
    <div className="mb-4 overflow-hidden rounded-md border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="space-y-3 p-4">
        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={togglePlayPause}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            className="flex size-10 items-center justify-center rounded-full bg-[#1d70b8] text-white hover:bg-[#003078]"
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{formatTime(time)}</span>
            <span>{duration ? formatTime(duration) : '--:--'}</span>
          </div>
          <input
            type="range"
            min="0"
            max={duration || 100}
            step={0.1}
            value={time}
            onChange={handleSeek}
            disabled={!duration}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 dark:bg-gray-700"
            style={{
              backgroundSize: `${(time / (duration || 1)) * 100}% 100%`,
              backgroundImage: 'linear-gradient(to right, #3b82f6, #3b82f6)',
            }}
          />
        </div>
      </div>
      <div className="flex justify-end bg-gray-50 p-2 dark:bg-gray-900">
        <a
          href={audioUrl}
          download={filename}
          className="govuk-link text-sm"
        >
          Save to Computer
        </a>
      </div>
    </div>
  )
}

const formatTime = (timeInSeconds: number): string => {
  if (Number.isNaN(timeInSeconds)) return '00:00'
  const minutes = Math.floor(timeInSeconds / 60)
  const seconds = Math.floor(timeInSeconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${seconds
    .toString()
    .padStart(2, '0')}`
}
const getDuration = async (blob: Blob) => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const arrayBuffer = await blob.arrayBuffer()
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
  return audioBuffer.duration
}
