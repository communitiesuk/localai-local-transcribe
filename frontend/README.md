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

### OpenAPI

After creating or modifying a FastAPI route, regenerate the frontend API client:

```bash
npm run openapi-ts
```

This command will:

1. Generate the latest OpenAPI specification (`fetch-openapi-spec`).
2. Generate the frontend API client from that specification (`generate-client`).
