# Shared API Types — Valentine Hotline

## How it works

The backend auto-generates an OpenAPI spec from FastAPI's Pydantic schemas.
The frontend uses this spec to generate TypeScript types, ensuring type safety across the stack.

## For Backend (Mahimai)

After changing any API schemas, regenerate the spec:

```bash
cd backend
python scripts/export_openapi.py
```

This outputs `shared/openapi.json`. Commit it.

## For Frontend (Friend)

### Setup (one time)

```bash
npm install -D openapi-typescript
```

Add to `package.json` scripts:

```json
{
  "scripts": {
    "generate:types": "npx openapi-typescript ../../shared/openapi.json -o src/api/types.generated.ts"
  }
}
```

### Generate types

```bash
npm run generate:types
```

This creates `src/api/types.generated.ts` with all request/response types.

### Usage in code

```ts
import type { components } from './api/types.generated';

type HeartProfile = components['schemas']['HeartProfileResponse'];
type SessionVerdict = components['schemas']['SessionVerdictResponse'];
```

### When to regenerate

Regenerate types whenever `shared/openapi.json` is updated (after backend schema changes).
