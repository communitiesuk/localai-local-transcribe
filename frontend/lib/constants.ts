export const API_PROXY_PATH = '/api/proxy'
export const USERS_PER_PAGE = 10

/**
 * Maximum size of an uploaded audio or video file, in bytes (5GB).
 */
export const MAX_UPLOAD_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024
export const MAX_UPLOAD_FILE_SIZE_LABEL = '5GB'

/** Maximum number of characters allowed in the agenda field. */
export const MAX_AGENDA_LENGTH = 500

/**
 * Feature flag for the local (IndexedDB) offline-recording persistence
 * feature.
 * See AIILG-1050.
 */
export const OFFLINE_RECORDINGS_ENABLED = false
