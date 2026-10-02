# Minute Frontend

### Development

To spin up the frontend

```
npm run dev
```

### Unit tests (Vitest)

```bash
npm run test
```

### Microphone defaults

Settings stores separate in-person and online microphone defaults per user in
this browser. Refreshing the device list preserves unsaved choices that remain
available and only falls back for disconnected devices; it does not save the draft.
Both recording flows wait for the account query to settle before applying a
saved default. Per-recording overrides remain independent of saved preferences.
If the account or saved preferences cannot be loaded, recording uses an available
microphone with a visible warning.

### OpenAPI

After creating or modifying a FastAPI route, regenerate the frontend API client:

```bash
npm run openapi-ts
```

This command will:

1. Generate the latest OpenAPI specification (`fetch-openapi-spec`).
2. Generate the frontend API client from that specification (`generate-client`).
