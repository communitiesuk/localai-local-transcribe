import { getFileExtensionFromBlob } from '@/lib/getFileExtension'
import { saveAs } from 'file-saver'

const twoDigits = (value: number) => String(value).padStart(2, '0')

export const getRecordingFileName = (
  file: Blob | File,
  recordedAt: Date = new Date()
): string => {
  const date = [
    recordedAt.getFullYear(),
    twoDigits(recordedAt.getMonth() + 1),
    twoDigits(recordedAt.getDate()),
  ].join('-')
  const time = [
    twoDigits(recordedAt.getHours()),
    twoDigits(recordedAt.getMinutes()),
    twoDigits(recordedAt.getSeconds()),
  ].join('')

  return `local-transcribe-recording-${date}-${time}.${getFileExtensionFromBlob(file)}`
}

export const downloadRecording = (
  file: Blob | File,
  recordedAt?: Date
): void => {
  saveAs(file, getRecordingFileName(file, recordedAt))
}
