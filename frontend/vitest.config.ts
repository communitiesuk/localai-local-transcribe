import { configDefaults, defineConfig } from 'vitest/config'

export default defineConfig({
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
