import { defineConfig, globalIgnores } from 'eslint/config'
import nextCoreWebVitals from 'eslint-config-next/core-web-vitals'
import nextTypescript from 'eslint-config-next/typescript'
import prettier from 'eslint-config-prettier'

export default defineConfig([
  globalIgnores(['lib/client/**/*']),
  ...nextCoreWebVitals,
  ...nextTypescript,
  prettier,
  {
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: '@/components/ui',
              message:
                'Direct imports from @/components/ui are restricted. Reach for @/components/govuk/* instead. Refer to components/govuk/README.md.',
            },
          ],
          patterns: [
            {
              group: ['@/components/ui/*'],
              message:
                'Imports from @/components/ui/* are restricted. Reach for @/components/govuk/* instead. Refer to components/govuk/README.md.',
            },
          ],
        },
      ],
    },
  },
  {
    files: [
      'components/ui/**',
      'components/audio/discard-dialog.tsx',
      'components/recent-meetings/**',
      'components/template-select/**',
      'components/layout/**',
      'app/transcriptions/**',
      'app/templates/components/editor/editor-toolbar.tsx',
      'app/templates/components/example-templates-dialog.tsx',
      'app/templates/components/user-templates-list.tsx',
      'components/transcription-title-editor.tsx',
      'components/status-icon.tsx',
      'components/download-button.tsx',
      'components/posthog-banner.tsx',
      'app/support/page.tsx',
      'app/privacy/page.tsx',
      'app/page.tsx',
      'app/user-management/**',
    ],
    rules: {
      'no-restricted-imports': 'off',
    },
  },
])
