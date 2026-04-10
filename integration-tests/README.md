# Integration Tests (Playwright)

This folder contains Node + Playwright integration tests for the app running on port `3000`.

## Setup

```bash
cd integration-tests
npm install
npm run install:browsers
```

## Run

Ensure the application is already running at `http://localhost:3000`, then:

```bash
npm test
```

Optional:

```bash
npm run test:headed
npm run test:ui
npm run test:report
```

## Configuration

- Default base URL: `http://localhost:3000`
- Override with: `BASE_URL=http://localhost:3000 npm test`
