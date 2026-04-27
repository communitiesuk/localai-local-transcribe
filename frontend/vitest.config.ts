import { configDefaults, defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'), // needs to align with alias in tsconfig.json
    },
  },
  test: {
    exclude: [...configDefaults.exclude, 'tests/e2e/**'],
    coverage: {
      provider: 'v8',
      enabled: true,
      reporter: ['text', 'html', 'cobertura'],
      reportsDirectory: './coverage',
    },
  },
})
