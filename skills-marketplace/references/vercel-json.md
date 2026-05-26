# Vercel Rewrites for Dynamic Routes (Static Output)

When deploying an Astro 5 static site that uses dynamic client-side routes (e.g. `/skills/{slug}`), you need a `vercel.json` to catch requests and serve the correct shell page.

## Pattern

Create `vercel.json` at the project root:

```json
{
  "rewrites": [
    { "source": "/skills/(.*)", "destination": "/skills/__fallback__" }
  ]
}
```

This rewrites ALL paths matching `/skills/{anything}` to a single generated page at `/skills/__fallback__/`. The React component on that page reads `window.location.pathname` to extract the actual slug.

## Requirements

1. **getStaticPaths must return at least one valid path** — in `[slug].astro`:
   ```astro
   export async function getStaticPaths() {
     return [{ params: { slug: '__fallback__' } }];
   }
   ```
   This generates `/skills/__fallback__/index.html` during build.

2. **The component reads the slug from the browser URL**, not from Astro params. In the React component:
   ```tsx
   const pathParts = window.location.pathname.split('/').filter(Boolean);
   const slug = pathParts[pathParts.length - 1];
   ```

3. **vercel.json must be committed** — it's part of the deploy configuration, not .gitignored.

## Testing

Visit `/skills/any-random-slug` — it should serve the fallback page without a 404. The React component will try to fetch API data for that slug and show an error if it doesn't exist.

## Pitfalls

- Without this rewrite, Vercel static returns a 404 for any slug not in getStaticPaths
- The rewrite only applies on Vercel — local dev (`npm run dev`) doesn't use vercel.json
- If you rename the fallback slug, update both the Astro page AND vercel.json
