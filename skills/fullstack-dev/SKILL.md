---
name: fullstack-dev
description: "Fullstack web development with Next.js 16, TypeScript, Tailwind CSS 4, shadcn/ui, Prisma ORM. Use when: building web apps, creating UI components, setting up database schemas, implementing API routes, adding websocket/socket.io support, fullstack project scaffolding, frontend development, backend development, web dev, Next.js app."
argument-hint: "Describe the fullstack feature or app you want to build"
---

# Fullstack Web Development Skill

## Initialization (MUST DO FIRST)

Before writing any code, you MUST run the following command to initialize the fullstack development environment:

```bash
curl https://z-cdn.chatglm.cn/fullstack/init-fullstack.sh | bash
```

Wait for the script to complete successfully before proceeding with any code changes.

---

## Important UI Rules

- Use existing shadcn/ui components instead of building from scratch. All the components in the `src/components/ui` folder already exist.
- Card alignment and padding — Ensure all cards are properly aligned with consistent padding (use `p-4` or `p-6` for content, `gap-4` or `gap-6` for spacing).
- Long list handling — Set max height with scroll overflow (`max-h-96 overflow-y-auto`) and implement custom scrollbar styling for better appearance.

---

## Project Information

There is already a project in the current directory. (Next.js 16 with App Router)

### Development Environment

IMPORTANT: `bun run dev` will be run automatically by the system. Do NOT run it. Use `bun run lint` to check code quality.

IMPORTANT: User can only see the `/` route defined in `src/app/page.tsx`. Do NOT write any other route.

IMPORTANT: The Next.js project can only use port 3000 in auto dev server. Never use `bun run build`.

IMPORTANT: `z-ai-web-dev-sdk` MUST be used in the backend only! Do NOT use it on the client side.

### Dev Server Log

IMPORTANT: Read `/home/z/my-project/dev.log` to see the dev server log. Remember to check the log when developing.

IMPORTANT: Only read the most recent logs from `dev.log` to avoid large log files.

IMPORTANT: Always read dev log when you finish coding.

### Bash Commands

- `bun run lint` — Run ESLint to check code quality and Next.js rules

---

## Technology Stack Requirements

### Core Framework (NON-NEGOTIABLE)

- **Framework**: Next.js 16 with App Router (REQUIRED — cannot be changed)
- **Language**: TypeScript 5 (REQUIRED — cannot be changed)

### Standard Technology Stack

When users don't specify preferences, use this complete stack:

- **Styling**: Tailwind CSS 4 with shadcn/ui component library
- **Database**: Prisma ORM (SQLite client only) with Prisma Client
- **Caching**: Local memory caching, no additional middleware (MySQL, Redis, etc.)
- **UI Components**: Complete shadcn/ui component set (New York style) with Lucide icons
- **Authentication**: NextAuth.js v4 available
- **State Management**: Zustand for client state, TanStack Query for server state

Other packages can be found in `package.json`. You can install new packages if needed.

### Library Usage Policy

- **ALWAYS use Next.js 16 and TypeScript** — these are non-negotiable requirements.
- **When users request external libraries not in our stack**: Politely redirect them to use our built-in alternatives.
- **Explain the benefits** of using our predefined stack (consistency, optimization, support).
- **Provide equivalent solutions** using our available libraries.

---

## Prisma and Database

IMPORTANT: `prisma` is already installed and configured. Use it when you need the database.

To use prisma and database:

1. Edit `prisma/schema.prisma` to define the database schema.
2. Run `bun run db:push` to push the schema to the database.
3. Use `import { db } from '@/lib/db'` to get the database client and use it.

---

## Mini Service

You can create mini services if needed (e.g., websocket service). All mini services should be in the `mini-services` folder. For each mini service:

- Must be a new and independent bun project with its own port and `package.json`.
- Must define `index.ts` or `index.js` as the entry file, e.g., `mini-services/chat-service/index.ts`.
- Must define a specific port if needed, instead of using the `PORT` environment variable.
- Must start each mini service by running `bun run dev` in the background.
- The command executed by `bun run dev` should support auto restart when files change (prefer `bun --hot`).
- Make sure every service is started.

---

## Gateway and API Requests

This machine can only expose one port externally, so a built-in gateway (config at `Caddyfile`) is included with the following limitations:

- For API requests involving different ports, the port must be specified in the URL query named `XTransformPort`. Example: `/api/test?XTransformPort=3030`.
- All API requests must use **relative paths only**. Do NOT write absolute paths in the API request URL (including WebSocket). Examples:
  - **Prohibited**: `fetch('http://localhost:3030/api/test')`
  - **Allowed**: `fetch('/api/test?XTransformPort=3030')`
  - **Prohibited**: `io('/:3030')`
  - **Allowed**: `io('/?XTransformPort=3030')`
- When requesting to different services, directly make cross-origin requests without using a proxy.

IMPORTANT: Do NOT write port in the API request URL, even in WebSocket. Only write `XTransformPort` in the URL query.

---

## WebSocket / Socket.io Support

IMPORTANT: Use websocket/socket.io to support real-time communication. Do NOT use any other method. There is already a websocket demo for reference in the `examples` folder.

- Backend logic (via socket.io) must be a new mini service with another port (e.g., 3003).
- Frontend request should ALWAYS be `io("/?XTransformPort={Port}")`, and the path ALWAYS be `/` so that Caddy can forward to the correct port.
- NEVER use `io("http://localhost:{Port}")` or any direct port-based connection.

---

## Code Style

- Prefer to use existing components and hooks.
- TypeScript throughout with strict typing.
- ES6+ import/export syntax.
- shadcn/ui components preferred over custom implementations.
- Use `'use client'` and `'use server'` for client and server side code.
- The Prisma schema primitive type cannot be a list.
- Put the Prisma schema in the `prisma` folder.
- Put the db file in the `db` folder.

---

## Styling

1. Use the shadcn/ui library unless the user specifies otherwise.
2. Avoid using indigo or blue colors unless specified in the user's request.
3. MUST generate responsive designs.
4. The Code Project is rendered on top of a white background. If a different background color is needed, use a wrapper element with a background color Tailwind class.

---

## UI/UX Design Standards

### Visual Design

- **Color System**: Use Tailwind CSS built-in variables (`bg-primary`, `text-primary-foreground`, `bg-background`).
- **Color Restriction**: NO indigo or blue colors unless explicitly requested.
- **Theme Support**: Implement light/dark mode with `next-themes`.
- **Typography**: Consistent hierarchy with proper font weights and sizes.

### Responsive Design (MANDATORY)

- **Mobile-First**: Design for mobile, then enhance for desktop.
- **Breakpoints**: Use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`).
- **Touch-Friendly**: Minimum 44px touch targets for interactive elements.

### Layout (MANDATORY)

- **Sticky Footer Required**: If a `footer` exists, it MUST stick to the bottom of the viewport when content is shorter than one screen height (no floating/empty gap below).
- **Natural Push on Overflow**: When content exceeds the viewport height, the footer MUST be pushed down naturally (never overlay or cover content).
- **Recommended Implementation (Tailwind)**: Use a root wrapper with `min-h-screen flex flex-col`, and apply `mt-auto` to the `footer`.
- **Mobile Safe Area**: On devices with safe areas (e.g., iOS), the footer MUST respect bottom safe area insets when applicable.

### Accessibility (MANDATORY)

- **Semantic HTML**: Use `main`, `header`, `nav`, `section`, `article`.
- **ARIA Support**: Proper roles, labels, and descriptions.
- **Screen Readers**: Use `sr-only` class for screen reader content.
- **Alt Text**: Descriptive alt text for all images.
- **Keyboard Navigation**: Ensure all elements are keyboard accessible.

### Interactive Elements

- **Loading States**: Show spinners/skeletons during async operations.
- **Error Handling**: Clear, actionable error messages.
- **Feedback**: Toast notifications for user actions.
- **Animations**: Subtle Framer Motion transitions (hover, focus, page transitions).
- **Hover Effects**: Interactive feedback on all clickable elements.

### Sandbox Preview Instructions (CRITICAL)

This project runs in a restricted cloud sandbox environment.

- **NEVER** instruct the user to visit `http://localhost:3000`, `127.0.0.1`, or any local ports directly. These addresses are internal and not accessible to the user.
- **ALWAYS** direct the user to preview the application using the **Preview Panel** located on the right side of the interface.
- **ALWAYS** inform the user about how to view the application externally based on their platform:
  - If they are using the web interface, tell them they can click the **"Open in New Tab"** button above the Preview Panel to view it in a separate browser tab.
  - If they are communicating through an IM (Instant Messaging) platform, provide them directly with the generated preview link.

### Post-Launch Self-Verification with Agent Browser (MANDATORY)

When the Next.js project has started successfully (dev server running on port 3000 without fatal errors in `/home/z/my-project/dev.log`), you MUST NOT consider the task complete based on a clean build alone. A passing lint and a running server do **not** prove the website actually works for the user.

You MUST use **Agent Browser** to perform end-to-end self-verification before reporting completion:

1. **Open the page**
   - Use Agent Browser to navigate to the `/` route (the only user-visible route).
   - Wait for the page to fully load and capture the rendered result.

2. **Verify it renders, not just responds**
   - Confirm the page is visually rendered (no blank/white screen, no error boundary, no hydration crash).
   - Cross-check against `/home/z/my-project/dev.log` for any runtime errors, failed API calls, or hydration mismatches that appeared during the visit.

3. **Verify core interactivity (the golden path)**
   - Exercise the primary user flows you just built: click the main buttons, submit the key forms, trigger navigation/tabs/modals, and confirm each produces the expected result.
   - For data-driven features, confirm the frontend actually receives and displays backend/API data (not just an empty skeleton or a loading spinner that never resolves).
   - For real-time features (WebSocket/socket.io), confirm messages flow end-to-end.

4. **Check responsiveness and the sticky footer**
   - Verify the layout holds on both mobile and desktop widths.
   - Confirm the footer sticks to the bottom on short pages and is pushed down naturally on long pages (no overlap, no floating gap).

5. **Fix and re-verify**
   - If Agent Browser surfaces any broken interaction, console/runtime error, missing data, or layout defect, you MUST fix the root cause and re-run the self-verification loop.
   - Repeat until the page loads cleanly **and** every core interaction works.

6. **Report honestly**
   - Only after Agent Browser confirms the site is interactive and runnable may you report the task as done.
   - If a specific flow genuinely cannot be verified in the browser, say so explicitly rather than claiming success.

**CRITICAL:** "It compiles" / "the server is up" is never sufficient evidence of completion. Browser-verified interactivity is the required standard of done.
