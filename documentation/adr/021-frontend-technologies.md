# ADR-021: Front-end Technology Stack

## Status

Accepted

Date of decision: 2026-05-08

## Context and Problem Statement

The current architecture of Local Transcribe (inherited from Minute) includes a Next.js application comprising of
a `frontend` server-side application and a client-side React SPA. The `frontend` application contributes to ongoing
running costs (by requiring Fargate container(s) to run), but hosts little business logic. We also expect much of the
UI of the client-side SPA to be altered (in some areas quite significantly) as we tailor the codebase to our target
use cases. This means we have a moment of opportunity to reconsider our front-end stack. What should we use?

## Considered Options

* Next.js app (standalone)
* Next.js app (static export)
* React SPA + Vite
* SvelteKit SPA (static export)
* Server-rendered MPA (with vanilla JS)

## Decision Outcome

Next.js app (standalone), because it is the least effort and poses the lowest delivery risk (by offering the shortest
required pause while unparallelisable rework happens, and by allowing flexibility in how far any refactoring/rewrite goes),
while still making it possible to achieve our goals.

## Pros and Cons of the Options

### Next.js app (standalone)

Next.js provides a framework for web applications. In standalone mode it exports both a client-side React application
and a minimal Node.js server bundle.

* Good, because this is the current set up, so requires no additional work
* Good, because it provides a simple, popular structure for the frontend (i.e. file-based routing, etc)
* Good, because it provides server-side rendering (SSR) out of the box
* Bad, because it requires an always on Fargate task to host the server-side component, which attracts cost
* Neutral, because it provides a natural BFF for the client-side application, but this is essentially currently unnecessary
* Good, because React is the dominant web UI rendering framework
* Good, because refactoring / rework can be tackled piecemeal
* Neutral, because modern React (server components) offers smaller bundle sizes than older React (especially with Next's per-page entry points)

### Next.js app (static export)
As above, but in static export mode, Next.js creates a static HTML and JS bundle for each page, which bootstraps the
same SPA as the standalone version, but with no server-side component.

* Bad, because it requires migration work (updating the export type, removing any server-side logic, exposing the API application, etc)
* Good, because it provides a simple, popular structure for the frontend (i.e. file-based routing, etc)
* Neutral, because it provides prerendering of static HTML (SSG) out of the box, but dynamic UI must be rendered by the JS
* Good, because it requires no server-side execution environment
* Good, because React is the dominant web UI rendering framework
* Good, because refactoring / rework can be tackled piecemeal
* Neutral, because modern React (server components) offers smaller bundle sizes than older React (especially with Next's per-page entry points)

### React SPA + Vite
Instead of the Next.js 'hybrid' approach, a more traditional React SPA is a single bundle (perhaps with some code splitting) with no
server-side component or prerendered HTML.

* Bad, because it requires similar migration work to a static Next.js app, plus configuration of Vite as a bundler
* Neutral, because it has no particular requirements on code structure
* Bad, because there is no SSR / SSG - UI is rendered only once the JS loads
* Good, because it requires no server-side execution environment
* Good, because React is the dominant web UI rendering framework
* Bad, because this option typically leads to the largest bundle sizes (without fairly significant effort to mitigate)

### SvelteKit SPA (static export)
SvelteKit provides an application framework built on top of Svelte (a competitor to React, but with a different philosophy). In static
export mode, it can produce static HTML and JS assets with no server-side component.

* Bad, because it will require a more substantial rewrite from React to Svelte - only pure JS logic would be reusable
* Good, because it provides a simple structure for the frontend, including file-based routing
* Neutral, because it provides prerendering of static HTML (SSG), but dynamic UI must be rendered by the JS
* Good, because it requires no server-side execution environment
* Neutral, because Svelte is less dominant than React, but is used by some other services within MHCLG
* Good, because Svelte typically results in small bundle sizes

### Server-rendered MPA (with vanilla JS)
A server-rendered MPA would move UI rendering back to a server-side application, with limited client-side JavaScript added only where needed.

* Bad, because it requires a substantial rewrite and a new server-rendered application architecture
* Good, because it aligns better with gov.uk technology standards
* Good, because it provides SSR by default
* Bad, because it requires an always-on server-side execution environment
* Bad, because rich interactive UI is harder to build and maintain without a client-side framework
* Good, because many services within MHCLG follow this pattern
* Good, because JS payload is typically small or zero