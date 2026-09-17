# HLD: Local audio retention cleanup for offline recordings

## Status
Draft

## Date
2026-09-17

## Overview
This change ensures that offline recordings stored locally are automatically cleaned up when they exceed the supported retention period. The system will delete audio files that are older than 14 days the first time a user opens Local Transcribe, and will continue to run periodic checks while the application remains open to delete any newly expired recordings.

This protects local disk space, keeps the app aligned with the offline storage policy, and avoids stale audio remaining in the local cache after it has expired.

## Background and problem statement
Local Transcribe stores audio recordings locally for offline workflows, including recordings captured or queued before upload completes. Because these recordings can accumulate over time, the app must enforce a retention policy so that stale files do not remain indefinitely on the user’s machine.

Without an expiry process, users may accumulate large volumes of old recordings, increasing storage use and creating unnecessary privacy/data-retention exposure in the local environment.

## Acceptance criteria
- When the user first loads Local Transcribe, any stored offline audio older than 2 weeks is deleted.
- Every X hours while Local Transcribe remains open, the app checks again and deletes any newly expired audio.

## User stories
- As a user, I want old offline recordings to be automatically removed so my local storage does not grow without bound.
- As a product owner, I want the app to enforce a consistent retention window for offline audio in line with policy requirements.
- As a support engineer, I want the cleanup to run automatically without requiring user intervention.

## Scope
### In scope
- Detecting local offline audio files and their timestamps.
- Deleting files older than 14 days on app startup.
- Scheduling a periodic cleanup job while the app stays open.
- Logging the cleanup results for troubleshooting and auditability.
- Handling missing, already deleted, or unreadable files safely.

### Out of scope
- Purging files from external storage or remote backend services.
- Changing the 14-day retention policy via app settings in this initial release.
- Deleting any non-offline audio that is still being actively processed.
- Handling data recovery for files already removed by the cleanup job.

## Design goals
- Enforce a clear retention window for local offline audio.
- Minimise operational complexity and user-visible impact.
- Be resilient to app restarts and temporary file-system issues.
- Keep the implementation lightweight and easy to test.

## Non-functional requirements
- Performance: Cleanup must not block the app UI during normal use.
- Reliability: Cleanup should not fail the app if one file cannot be removed.
- Security and privacy: Only files in the offline audio retention path are eligible for deletion.
- Observability: Log the number of files removed and any failures for diagnosis.
- Maintainability: Retention logic should be isolated into a single cleanup service.

## High-level design

### Components
1. Local offline audio storage directory
   - A dedicated local folder used to store audio recordings that have not yet been uploaded or processed.
   - Each file has a creation or modification timestamp used for expiry checks.

2. Retention cleanup service
   - Responsible for scanning the offline audio directory.
   - Evaluating whether each file is older than 14 days.
   - Deleting expired files and tracking results.

3. App startup trigger
   - Runs once when Local Transcribe loads.
   - Performs an immediate cleanup pass to remove any stale files created before the app was opened.

4. Background scheduler
   - Runs while the app remains open.
   - Executes a recurring cleanup pass every X hours.
   - Uses a timer or scheduler service that is cancelled when the app closes.

### Storage and retention model
The app should treat offline audio retention as a filesystem TTL policy:
- Retention period: 14 days
- Comparison basis: file creation time or last modified time, whichever is the app’s canonical metadata source
- Candidate set: only files beneath the dedicated offline audio directory
- Exclusions: active processing folders, uploaded files, or records already confirmed as uploaded and no longer local-only

### Proposed lifecycle
1. The app starts.
2. The startup hook calls `cleanupExpiredOfflineAudio()`.
3. The cleanup module lists files in the offline audio directory.
4. It filters for files older than 14 days.
5. It deletes expired files and logs the outcome.
6. The app starts a periodic scheduler with interval = X hours.
7. Each scheduled tick repeats the same cleanup check and removes newly expired recordings.
8. When the app is closed, the scheduler is stopped and resources are released.

## Detailed design

### Startup behaviour
On app initialisation:
- Validate the offline audio directory exists.
- If it does not exist, create it or skip cleanup with a debug log.
- Run the cleanup routine immediately.
- Continue user interaction without blocking the main UI thread.

This ensures that the first-time-load acceptance criterion is met without requiring the user to perform an action.

### Periodic behaviour while the app remains open
A background scheduler runs every X hours. Recommended default: 6 hours. The exact interval should be configurable in a single app setting, but the default must remain safe and simple.

Pseudo logic:

```text
CONST RETENTION_DAYS = 14
CONST CLEANUP_INTERVAL_HOURS = 6   // configurable, X in the AC

function cleanupExpiredOfflineAudio():
    offlineAudioFiles = listLocalOfflineAudioFiles()
    for each file in offlineAudioFiles:
        if fileAgeInDays(file) > RETENTION_DAYS:
            try:
                delete(file)
                logInfo("Removed expired local audio", { file, ageDays })
            catch error:
                logWarn("Failed to remove expired local audio", { file, error })

function onAppLoad():
    cleanupExpiredOfflineAudio()
    startRecurringTimer(CLEANUP_INTERVAL_HOURS, cleanupExpiredOfflineAudio)

function onAppClose():
    stopRecurringTimer()
```

### Deletion safety rules
- Only delete files in the offline audio folder, never user-selected uploads or files outside the retention scope.
- Do not delete files with active processing flags or explicit “keep” markers.
- If a file cannot be deleted due to permissions or lock issues, log it and move on without crashing the app.
- Treat deletion as best-effort; the goal is to remove stale files where possible, not to fail the application if one file is locked.

## Sequence flow

### Initial app load
```text
User opens Local Transcribe
  -> App boot completes
  -> Startup hook triggers cleanupExpiredOfflineAudio()
  -> Scanner enumerates offline audio directory
  -> Files older than 14 days are deleted
  -> Cleanup summary is logged
  -> User can continue working normally
```

### Periodic app-open cleanup
```text
Timer fires after X hours while app is open
  -> cleanupExpiredOfflineAudio() runs
  -> Scanner checks offline audio directory
  -> Newly expired files are deleted
  -> Results are logged
  -> Timer remains active until app closes
```

## Error handling and resilience
- If the local audio folder does not exist, the process should exit cleanly with a debug log instead of throwing an error.
- If a file is missing by the time deletion is attempted, treat it as already cleaned up and continue.
- If disk access fails for a single file, log the exception and continue processing remaining files.
- If the scheduler cannot start, log the issue and continue app operation; a later restart will still trigger the startup cleanup.

## Observability
The implementation should emit logs at INFO/WARN level with enough context to support troubleshooting:
- total files scanned
- total files deleted
- total files skipped due to errors
- file paths for failures
- retention period applied
- next scheduled cleanup time

This gives support and engineering teams visibility without exposing user audio content in logs.

## Security and privacy considerations
- The cleanup routine should operate only on the app’s offline storage area, not on arbitrary user data directories.
- It must never delete files that are part of active or queued transcription workflows unless they are explicitly in the offline retention path.
- Logs should avoid storing audio metadata or content; only file name, path, and timestamps should be recorded as needed for debugging.
- The retention policy should be documented in the app’s privacy and retention guidance so users understand why local recordings expire.

## Testing strategy
### Unit tests
- Given an offline audio directory with files older than 14 days, cleanup deletes them.
- Given files newer than 14 days, cleanup leaves them in place.
- Given a missing file or inaccessible file, cleanup does not crash.
- Given the app startup trigger, the cleanup routine fires once on first load.
- Given the scheduler, the recurring cleanup runs at the configured interval.

### Integration tests
- Verify cleanup works against a real temporary offline directory on a test machine.
- Confirm startup and background timer behaviour with simulated clock/time injection.
- Validate that files outside the offline retention directory are not touched.

## Risks and mitigations
### Risk: Over-deleting files
Mitigation: Restrict deletion to the dedicated offline audio directory and never delete active/in-flight recordings.

### Risk: Timer drift or missed intervals
Mitigation: Use a reliable scheduler and a startup cleanup as a fallback so expired files are still deleted even if the interval is missed.

### Risk: Files locked by the OS
Mitigation: Catch file deletion failures and continue processing; log the issue for support.

### Risk: User confusion about data loss
Mitigation: Communicate the 14-day retention policy in the app UI and privacy documentation.

## Open questions
- Should the retention interval be hard-coded or configurable in app settings? (recommended: configurable but default 14 days)
- Should cleanup be based on file creation time or last modified time to match the recording lifecycle semantics?
- Is there a need for a user-facing warning before deletion when a file is close to expiry?

## Recommendation
Proceed with a single, isolated cleanup service that runs on startup and on a configurable periodic timer while the app remains open. This approach satisfies the acceptance criteria with low complexity, minimal UI impact, and clear operational behaviour.
