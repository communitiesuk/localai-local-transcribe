export const EMAIL_MISSING_MESSAGE = 'Enter an email address'
export const EMAIL_FORMAT_MESSAGE =
  'Enter an email address in the correct format, like name@example.gov.uk'
export const EMAIL_LOCAL_PART_LENGTH_MESSAGE =
  'The part of the email address before the @ symbol must be 64 characters or fewer'
export const EMAIL_LENGTH_MESSAGE =
  'Email address must be 254 characters or fewer'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/
const MAX_LOCAL_PART_LENGTH = 64
const MAX_EMAIL_LENGTH = 254

export default function validateEmail(email: string): string | null {
  if (!email) {
    return EMAIL_MISSING_MESSAGE
  }

  if (!EMAIL_PATTERN.test(email)) {
    return EMAIL_FORMAT_MESSAGE
  }

  if (email.split('@')[0].length > MAX_LOCAL_PART_LENGTH) {
    return EMAIL_LOCAL_PART_LENGTH_MESSAGE
  }

  if (email.length > MAX_EMAIL_LENGTH) {
    return EMAIL_LENGTH_MESSAGE
  }

  return null
}
