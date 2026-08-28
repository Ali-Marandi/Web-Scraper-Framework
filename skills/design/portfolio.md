# Portfolio / Personal Website

This reference is for portfolio sites, personal websites, and creative showcases. Consult it when the user asks to build a site that presents a person and their work.

---

## The Two Non-Negotiables

Everything else is flexible, but these two must be true:

1. **Work first.** The visitor must see actual work — not a bio, not a mission statement, not a loading animation — within the first viewport. The work IS the hero. If you're designing an "About Me" section before the work is visible, you're building a resume, not a portfolio.

2. **Emotion in 2 seconds.** Before the visitor reads a single word, they should feel something — curiosity, awe, tension, delight. This comes from an unusual navigation concept, an unexpected layout, a bold typographic choice, or the work itself presented at full impact. If the first 2 seconds feel like "a website," the design has already failed.

---

## Choose a Structure

Portfolio sites have more structural freedom than any other type of website. The work's nature should dictate the structure — don't default to "grid of thumbnails."

### A. The Index List
Projects shown as text rows — title, year, category. Hovering a row reveals a preview image that follows the cursor or fills a dedicated zone. Dense, editorial, fast to scan.
**Best for:** Large bodies of work (10+), designers who want to signal breadth and taste. Also works well for mixed-discipline portfolios where thumbnail sizes would be inconsistent.
**The move:** The hover-preview image makes the visitor feel like they're "discovering" each project rather than being shown it.

### B. Full-Bleed Showcase
One project occupies the entire viewport. Scroll or swipe transitions to the next. Each project gets its own atmosphere — background color, typography weight, even ambient sound.
**Best for:** Visual-heavy work — photography, branding, motion design. Small portfolios (4-6 projects) where each piece deserves full attention.
**The move:** Per-project theming. When the background shifts from warm ivory to deep navy between projects, the designer proves they can inhabit different brand worlds.

### C. Spatial / Non-Linear
Projects exist as points, clusters, or objects in a 2D/3D space. No list order, no grid. Navigation is exploration — the visitor chooses where to go by moving through space.
**Best for:** Conceptual work, art direction, experimental portfolios. Small portfolios where spatial relationships between projects add meaning.
**The move:** The navigation model itself IS the portfolio. A coordinate system with crosshairs, a room you walk through, a map you explore — the metaphor communicates the designer's thinking.

### D. The Product-as-Portfolio
The website is not a showcase OF work — it IS the work. A functional tool, an interactive experience, a playable thing. Past projects may be listed elsewhere, but the site itself demonstrates capability.
**Best for:** Developers, creative technologists, interaction designers. People whose skill is building things, not just showing images of things.
**The move:** The visitor uses the portfolio before they read it. The proof of skill is in their hands.

### E. Fixed Identity + Scrollable Work
A fixed panel (side or top) holds the person's identity — name, role, contact. The rest of the screen is dedicated to browsable work in any format (horizontal scroll, vertical scroll, grid).
**Best for:** General-purpose portfolios where both identity and work need to coexist. Freelancers and job-seekers who need quick access to contact info.
**The move:** The identity panel is always visible, so the visitor never loses context about WHO made this work. The panel becomes a quiet signature.

**Anti-pattern: The Marketing Page Portfolio.**
Hero section with big tagline → grid of thumbnail cards → about section → testimonials → contact form → footer. This is a business landing page wearing a portfolio costume. It signals "I downloaded a template," not "I designed this."

---

## How to Present Work

### On the Home Page

The home page presentation should make the visitor want to click into a project. This means:

- **Lead with the strongest piece, not the most recent.** The first visible project is the one the visitor will judge you by. Chronological order is lazy; curated order shows taste.
- **Vary the visual weight.** If every project thumbnail is the same size, all work looks equivalent. Give the hero project more space, let secondary work be smaller. Hierarchy signals confidence.
- **Show the work, not a mockup of the work.** A screenshot inside a laptop mockup inside a browser frame adds three layers of distance between the visitor and the actual design. Show the work directly.
- **Cap at 4-8 projects.** Showing everything signals inability to edit. A tightly curated selection says "I have more, but these are the ones that matter."

### Project Detail Pages

Every portfolio MUST have project detail pages. A portfolio without details is a slideshow. Details are where the visitor decides "this person thinks clearly" or "this person just makes things look nice."

**What a project detail page needs:**

1. **The work at full scale.** Large images, multiple views, real screenshots — not thumbnails.
2. **The narrative (short).** Three paragraphs maximum: What was the challenge? What did you do? What was the result? This is not a case study — it's a summary that proves you can think, not just execute.
3. **Structured metadata.** Role, team size, timeline, tools — in a sidebar or compact block. This is where monospace labels work well.
4. **Navigation between projects.** Previous/next links so the visitor can browse without going back to the index. Keep them in the flow.
5. **A way back.** Close button, back link, or ESC key. Never trap someone in a detail view.

**What a project detail page does NOT need:**
- A "problem statement" section with 3 paragraphs about the client's industry
- A "process" section with wireframe screenshots and sticky-note photos
- Testimonial quotes from clients
- "Want to see more? Let's chat!" CTAs after every project

---

## Identity & Bio

The bio should feel like a person wrote it, not a LinkedIn profile generator.

**The 2-sentence rule:** You get 2 sentences to say who you are. Make them count. Specifics beat adjectives.

- Bad: "I'm a passionate designer who loves crafting beautiful experiences."
- Good: "Senior visual designer at Deloitte Digital. Former pianist — my thinking is both visual and structural."
- Good: "I design AI products in Beijing. Previously made tools for researchers at Zhipu AI."

**Placement:** The bio should be accessible but NOT the first thing you see. Work first, identity second. Common good placements:
- Fixed side panel (always visible but secondary to the work area)
- Accessible via a single click/link from the home page
- At the bottom of the page, after the work
- In an overlay triggered by clicking the name

**Credentials embedded, not shouted.** "Awwwards Jury member since 2022" as a small caption under the bio, not a banner at the top of the page.

---

## Portfolio-Specific Moves

### Dynamic theming per project
When a visitor scrolls from one project to the next, the background color, accent color, and mood shift to match that project's brand. This is the single strongest signal of design capability — you're proving you can work in multiple visual languages, not just your own.

### Taste as proof
Curating other people's work — a list of music videos you love, a collection of typefaces you admire, a reading list — demonstrates taste and cultural awareness without being self-promotional. The best designers know good work when they see it.

### The entrance moment
A brief, deliberate loading or entrance sequence sets the mood before the content appears. Not a loading spinner — a percentage counter, a text reveal, a quick animation that establishes the site's personality in 1-2 seconds. Must be fast (under 2 seconds) or it becomes an obstacle.

### Custom cursor or interaction pattern
A non-default cursor (crosshair, dot, custom shape), a hover preview that follows the mouse, or a non-standard interaction model signals "this was built from scratch." Even subtle: making the cursor change to a "view" icon when hovering over projects.

### Contact as conversation, not form
A mailto link feels human. A contact form feels corporate. Portfolio sites should feel like you're reaching out to a person, not submitting a request to a company. "lilu@example.com" beats a 5-field form every time.

### Oversized type as the hero
Set the name, role, or a one-line statement at display scale — `clamp()` scaling up to ~12–18vw — so it fills most of the first viewport and the text itself is the hero, no image required. Keep body/meta small (14–16px) so the size jump is 8–10×; that contrast is what reads as confident, not the big number alone. Pair a display face for the giant type with a smaller mono face for labels/coordinates/year tags.

### Dark statement break for rhythm
Don't let the page be one flat light scroll. Insert one or two full-bleed dark sections (a manifesto line, a single statement, a section divider) between lighter content — same type system, reversed colors. These are tempo beats: the visitor feels the page breathe in and out instead of scrolling a uniform document. One or two only; more kills the effect.

### Asymmetric layout, not centered safety
Default to off-balance grids — `1.2fr 1fr`, `2fr 1fr 1fr`, or content pinned to one edge with deliberate empty space on the other — instead of centered `1fr 1fr` symmetry. Let a hero image bleed off one side, let a heading hang into the margin. The tension and editorial feel come from the imbalance; centered-everything is what makes a page look like a template.

---

## Completeness Checklist

A portfolio site is finished when:

- [ ] Actual work is visible in the first viewport — no bio-first, no loading-first
- [ ] Every project on the home page has a detail page with full images and narrative
- [ ] Previous/next navigation exists between project details
- [ ] There is a way to return from detail view to the index (back link + ESC key)
- [ ] The bio is 2-3 sentences of specific, human text — not LinkedIn prose
- [ ] Contact is a real email address or link, not `href="#"`
- [ ] The strongest project is shown first, not the most recent
- [ ] No more than 8 projects on the home page
- [ ] The site works on mobile — the structure adapts, not just shrinks
- [ ] There is one memorable element someone would describe to a friend: "the one where projects are dots on a grid" / "the one where the background color changes per project"

---

## How this fits the Design Skill flow

This file is the portfolio scenario reference. It plugs into the main `SKILL.md` flow — it does not replace it.

- **Scene type.** A portfolio is an **expressive** scene. Per `SKILL.md` Creative Context, before building, make a concrete visual commitment (which structure A–E, the hero treatment, the one signature move) — written as specific elements and actions, not adjectives like "bold" or "premium". The "one memorable element" in the checklist above IS that commitment.
- **Don't fall back to a mature design system here.** The Mature System Fallback in `SKILL.md` is for restrained/no-style scenes (dashboards, tools). A portfolio is expressive — design it from the structure choices above, not from a generic system baseline.
- **Templates.** If `design-templates/INDEX.md` has a matching portfolio/personal-site template, it may be used as a starting skeleton — but the structure choice (A–E) and the signature move still drive the result; never ship the template's layout unchanged.

## Creative Context (from SKILL.md)

For open-ended requests, complete these before generating:

- `creative_positioning` — what this person should be known for (one line).
- `first_impression` — what the visitor should feel in the first 2 seconds (tie to "Emotion in 2 seconds").
- `anti_default` — which generic portfolio reflex to avoid (usually the Marketing-Page-Portfolio anti-pattern).

The artifact must visibly reflect this. Don't print the context unless asked.

## References — load only when triggered

Don't read these by default. A first draft usually needs this file + a selected style/design-system reference if any + only 1–3 triggered craft files.

- `horizontal-craft/chinese-typography.md` — substantial Chinese text. **If the page has Chinese, its font rules are mandatory**: any named font must actually be loaded (`<link>` or `@font-face`), and a Chinese page's `font-family` must contain a CJK font name — never let a Latin font fall straight to `system-ui`. Font choice/loading: `horizontal-craft/fonts.md`.
- `horizontal-craft/color.md` — no color direction is given.
- `horizontal-craft/icon-system.md` — UI/social/navigation icons are used. No emoji as icons.
- `horizontal-craft/animation-discipline.md` — entrance choreography, scroll reveal, hover, custom cursor, or theming transitions (the Portfolio-Specific Moves above). For an expressive scene a fully static page is under-delivered; take paste-ready entrance CSS from here.
- `horizontal-craft/technique-library.md` — advanced technique genuinely serves the work: 3D, shader, rich scroll narrative, custom data-viz, spatial navigation (structure C).
- `design-system-reference.md` — the user gives a brand/style reference, DESIGN.md, screenshots, or a prior artifact to follow.
- `canvas-and-device.md` — fixed export size, device frame, or screenshot-showcase constraints.

## Final Gate

Run `quality-gate.md` as the blocking final checklist before delivery. It owns the global checks (accessibility, `:focus-visible`, reduced-motion, dead links, placeholder logic, Design Compliance comments, version/handoff) — don't duplicate them here.

Portfolio-specific gate, on top of the Completeness Checklist above:

- the strongest work is visually prioritized; projects are not flattened into equal cards;
- no invented credentials, employers, clients, testimonials, awards, metrics, outcomes, logos, or press;
- role / domain / point of view are clear within the first screen;
- the distinctiveness test passes: cover the person's name — could this be anyone's portfolio? If yes, revise;
- any motion or special technique serves the person's identity or work, not novelty.

## Handoff

Use the standard Design Skill delivery, export, and version-management flow (`export.md`). This file does not define a separate portfolio handoff.
