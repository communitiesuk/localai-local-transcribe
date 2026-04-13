import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Paths
const SETTINGS_PY = path.join(__dirname, '..', 'common', 'settings.py')
const OUTPUT_JSON = path.join(__dirname, 'app', 'settings', 'constants.json')

function sync() {
  if (!fs.existsSync(SETTINGS_PY)) {
    console.error(`Error: ${SETTINGS_PY} not found`)
    // Don't exit with error here to allow build to continue if constants are already there?
    // Actually, better to fail fast so we don't have stale constants.
    process.exit(1)
  }

  const content = fs.readFileSync(SETTINGS_PY, 'utf8')
  const constants = {}

  const minWordMatch = content.match(/MIN_WORD_COUNT_FOR_SUMMARY\s*=\s*(\d+)/)
  if (minWordMatch) {
    constants['MIN_WORD_COUNT_FOR_SUMMARY'] = parseInt(minWordMatch[1], 10)
  }

  const guardrailMatch = content.match(/GUARDRAIL_THRESHOLD\s*=\s*([\d\.]+)/)
  if (guardrailMatch) {
    constants['GUARDRAIL_THRESHOLD'] = parseFloat(guardrailMatch[1])
  }

  if (Object.keys(constants).length === 0) {
    console.error('Error: No constants found in settings.py')
    process.exit(1)
  }

  // Create directory if it doesn't exist
  const dir = path.dirname(OUTPUT_JSON)
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }

  // Write JSON
  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(constants, null, 2) + '\n')

  console.log(`Successfully synced constants to ${OUTPUT_JSON}`)
  console.log(JSON.stringify(constants, null, 2))
}

sync()
pre
