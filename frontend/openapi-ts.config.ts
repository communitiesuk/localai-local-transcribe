import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: {
    path: './openapi.json',
    filters: { tags: { exclude: ['Healthcheck'] } },
  },
  output: { path: 'lib/client', postProcess: ['prettier'] },
  plugins: ['@hey-api/client-next', '@tanstack/react-query'],
})
