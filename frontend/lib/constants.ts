export const API_PROXY_PATH = '/api/proxy'
export const USERS_PER_PAGE = 10

/**
 * Maximum size of an uploaded audio or video file, in bytes (5GB).
 */
export const MAX_UPLOAD_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024
export const MAX_UPLOAD_FILE_SIZE_LABEL = '5GB'

/**
 * Maximum length of a single recording, in milliseconds (2 hours).
 */
export const MAX_RECORDING_DURATION_MS = 2 * 60 * 60 * 1000
export const MAX_RECORDING_DURATION_LABEL = '2 hours'

/**
 * Stop a recording this far short of the cap. The length only updates about once a second,
 * so stopping on the cap itself can land just over it if a tick is delayed.
 */
export const RECORDING_STOP_HEADROOM_MS = 30 * 1000
export const AUTO_STOP_RECORDING_DURATION_MS =
  MAX_RECORDING_DURATION_MS - RECORDING_STOP_HEADROOM_MS

/** Maximum number of characters allowed in the agenda field. */
export const MAX_AGENDA_LENGTH = 500

/** Formats Azure Speech documents as supported, plus the video containers recordings arrive in. */
export const ACCEPTED_UPLOAD_FORMATS: Record<string, string[]> = {
  'audio/wav': ['.wav'],
  'audio/x-wav': ['.wav'],
  'audio/mpeg': ['.mp3'],
  'audio/mp4': ['.m4a'],
  'audio/x-m4a': ['.m4a'],
  'audio/aac': ['.aac'],
  'audio/flac': ['.flac'],
  'audio/x-flac': ['.flac'],
  'audio/ogg': ['.ogg', '.opus'],
  'audio/opus': ['.opus'],
  'audio/webm': ['.webm'],
  'audio/amr': ['.amr'],
  'audio/x-ms-wma': ['.wma'],
  'video/mp4': ['.mp4', '.m4v'],
  'video/quicktime': ['.mov'],
  'video/webm': ['.webm'],
  'video/x-ms-wmv': ['.wmv'],
}

/**
 * Feature flag for the local (IndexedDB) offline-recording persistence
 * feature.
 * See AIILG-1050.
 */
export const OFFLINE_RECORDINGS_ENABLED = false
