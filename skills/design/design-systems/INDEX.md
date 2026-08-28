# Design System Reference Index

Use this index to select one relevant design reference.

Do not load all references. Choose the closest match to the user's explicit request and active artifact.

## Library Layout

```text
SKILLS/design/design-systems/
├── INDEX.md
├── style-skills/
│   └── [style-name]/
│       ├── DESIGN.md
│       ├── components.html  # optional
│       └── tokens.css       # optional
└── brand-inspiration/
    └── [brand-name]/
        ├── DESIGN.md
        ├── components.html  # optional
        └── tokens.css       # optional
```

## Selection Rule

- Use `style-skills/` when the user asks for a general visual style, mood, UI style, product surface style, or reusable design recipe.
- Use `brand-inspiration/` when the user references a public brand or product style.
- Treat brand references as inspiration only. Do not copy logos, proprietary layouts, branded assets, or distinctive commercial UI.
- If a reference includes `components.html` or `tokens.css`, use those as stronger implementation references when the user asks for component fidelity.
- Do not combine multiple references unless the user explicitly asks.

---

# Style Skills

Path: `SKILLS/design/design-systems/style-skills/`

Available style skills:

> **按风格气质选(用户说"清新/高级/科技/复古/温暖/极简"等模糊词而非点名系统时)**：
> 读同目录 `index.json`，按每个条目的 `mood` / `formality` / `scheme` 标签匹配用户描述，
> 选气质最接近的 style-skill。下面列表的一句话描述只是补充；`index.json` 的标签才是匹配主依据。

- **agentic** — Path: `style-skills/agentic/`
- **ant** — Path: `style-skills/ant/` — Ant Design / enterprise component-oriented UI; use when user explicitly asks for Ant Design or antd-like enterprise UI.
- **application** — Path: `style-skills/application/` — Product/application UI patterns.
- **artistic** — Path: `style-skills/artistic/`
- **atelier-zero** — Path: `style-skills/atelier-zero/` — Minimal studio / atelier-style visual system.
- **bento** — Path: `style-skills/bento/`
- **bold** — Path: `style-skills/bold/`
- **brutalism** — Path: `style-skills/brutalism/` — Raw structure, direct hierarchy, intentionally rough visual energy.
- **cafe** — Path: `style-skills/cafe/`
- **claude** — Path: `style-skills/claude/`
- **claymorphism** — Path: `style-skills/claymorphism/`
- **clean** — Path: `style-skills/clean/` — Clean, neutral, orderly composition.
- **codex** — Path: `style-skills/codex/`
- **colorful** — Path: `style-skills/colorful/`
- **contemporary** — Path: `style-skills/contemporary/`
- **corporate** — Path: `style-skills/corporate/` — Business-facing, formal, structured visual language.
- **cosmic** — Path: `style-skills/cosmic/`
- **creative** — Path: `style-skills/creative/`
- **dashboard** — Path: `style-skills/dashboard/` — Dense data/application interface patterns.
- **default** — Path: `style-skills/default/` — Neutral general-purpose design system fallback. — includes components, tokens
- **dithered** — Path: `style-skills/dithered/`
- **doodle** — Path: `style-skills/doodle/`
- **dramatic** — Path: `style-skills/dramatic/`
- **editorial** — Path: `style-skills/editorial/` — Magazine-like typography, strong content rhythm, art-directed layout.
- **elegant** — Path: `style-skills/elegant/`
- **energetic** — Path: `style-skills/energetic/`
- **enterprise** — Path: `style-skills/enterprise/` — B2B/enterprise clarity, dense but controlled components.
- **expressive** — Path: `style-skills/expressive/`
- **fantasy** — Path: `style-skills/fantasy/`
- **fiction** — Path: `style-skills/fiction/`
- **flat** — Path: `style-skills/flat/`
- **friendly** — Path: `style-skills/friendly/`
- **futuristic** — Path: `style-skills/futuristic/`
- **glassmorphism** — Path: `style-skills/glassmorphism/` — Translucent layered surfaces; use sparingly.
- **gradient** — Path: `style-skills/gradient/`
- **hud** — Path: `style-skills/hud/` — Heads-up-display / operational interface aesthetic.
- **immersive** — Path: `style-skills/immersive/`
- **impeccable** — Path: `style-skills/impeccable/`
- **levels** — Path: `style-skills/levels/`
- **lingo** — Path: `style-skills/lingo/`
- **luxury** — Path: `style-skills/luxury/` — Premium spacing, refined contrast, elegant restraint.
- **material** — Path: `style-skills/material/` — Material Design-like component system and interaction clarity.
- **matrix** — Path: `style-skills/matrix/`
- **minimal** — Path: `style-skills/minimal/` — Restrained, low-decoration, content-first layout.
- **mission-control** — Path: `style-skills/mission-control/` — Command center and control-room inspired product surfaces.
- **modern** — Path: `style-skills/modern/`
- **mono** — Path: `style-skills/mono/`
- **neobrutalism** — Path: `style-skills/neobrutalism/` — Bold borders, high contrast, raw visual energy.
- **neon** — Path: `style-skills/neon/`
- **neumorphism** — Path: `style-skills/neumorphism/`
- **pacman** — Path: `style-skills/pacman/`
- **paper** — Path: `style-skills/paper/` — Tactile paper-like surfaces and editorial warmth.
- **parchment** — Path: `style-skills/parchment/` — Warm parchment, ink-blue accent, serif-led print/editorial system for formal & long-form documents (résumé, report, white paper, letter). Pairs with content-page; not a product-UI style.
- **perspective** — Path: `style-skills/perspective/`
- **premium** — Path: `style-skills/premium/`
- **professional** — Path: `style-skills/professional/` — Conservative professional presentation, clarity, trust, low-risk polish.
- **publication** — Path: `style-skills/publication/`
- **refined** — Path: `style-skills/refined/`
- **retro** — Path: `style-skills/retro/` — Nostalgic visual language.
- **riso** — Path: `style-skills/riso/`
- **sega** — Path: `style-skills/sega/`
- **shadcn** — Path: `style-skills/shadcn/` — Modern Tailwind/shadcn-style component composition; use when user asks for shadcn/ui or modern composable UI.
- **simple** — Path: `style-skills/simple/`
- **sketch** — Path: `style-skills/sketch/`
- **skeumorphism** — Path: `style-skills/skeumorphism/`
- **sleek** — Path: `style-skills/sleek/`
- **spacious** — Path: `style-skills/spacious/`
- **storytelling** — Path: `style-skills/storytelling/`
- **terracotta** — Path: `style-skills/terracotta/`
- **tetris** — Path: `style-skills/tetris/`
- **totality-festival** — Path: `style-skills/totality-festival/`
- **trading-terminal** — Path: `style-skills/trading-terminal/` — Dense financial/trading terminal aesthetic.
- **urdu** — Path: `style-skills/urdu/`
- **vibrant** — Path: `style-skills/vibrant/`
- **vintage** — Path: `style-skills/vintage/`
- **warm-editorial** — Path: `style-skills/warm-editorial/` — Warm editorial system with human texture.

---

# Brand Inspiration

Path: `SKILLS/design/design-systems/brand-inspiration/`

Use only as high-level inspiration unless the user provides owned assets or an official/open design system.

Available brand inspiration references:

- **airbnb** — Path: `brand-inspiration/airbnb/` — Warm human-centered marketplace feel. — includes components, tokens
- **airtable** — Path: `brand-inspiration/airtable/`
- **apple** — Path: `brand-inspiration/apple/` — Restraint, premium spacing, clear typography, product focus. — includes components, tokens
- **arc** — Path: `brand-inspiration/arc/`
- **binance** — Path: `brand-inspiration/binance/`
- **bmw** — Path: `brand-inspiration/bmw/`
- **bmw-m** — Path: `brand-inspiration/bmw-m/`
- **bugatti** — Path: `brand-inspiration/bugatti/`
- **cal** — Path: `brand-inspiration/cal/`
- **canva** — Path: `brand-inspiration/canva/`
- **cisco** — Path: `brand-inspiration/cisco/`
- **claude** — Path: `brand-inspiration/claude/`
- **clay** — Path: `brand-inspiration/clay/`
- **clickhouse** — Path: `brand-inspiration/clickhouse/`
- **cohere** — Path: `brand-inspiration/cohere/`
- **coinbase** — Path: `brand-inspiration/coinbase/`
- **composio** — Path: `brand-inspiration/composio/`
- **cursor** — Path: `brand-inspiration/cursor/` — includes components, tokens
- **discord** — Path: `brand-inspiration/discord/` — Community product UI with playful but structured interface patterns. — includes components, tokens
- **duolingo** — Path: `brand-inspiration/duolingo/`
- **elevenlabs** — Path: `brand-inspiration/elevenlabs/`
- **expo** — Path: `brand-inspiration/expo/`
- **ferrari** — Path: `brand-inspiration/ferrari/`
- **figma** — Path: `brand-inspiration/figma/` — Collaborative product energy, structured color, approachable creation. — includes components, tokens
- **framer** — Path: `brand-inspiration/framer/`
- **github** — Path: `brand-inspiration/github/` — Developer collaboration, code/product clarity, utility-first UI. — includes components, tokens
- **hashicorp** — Path: `brand-inspiration/hashicorp/`
- **huggingface** — Path: `brand-inspiration/huggingface/`
- **ibm** — Path: `brand-inspiration/ibm/`
- **intercom** — Path: `brand-inspiration/intercom/`
- **kami** — Path: `brand-inspiration/kami/` — includes components, tokens
- **kraken** — Path: `brand-inspiration/kraken/`
- **lamborghini** — Path: `brand-inspiration/lamborghini/`
- **linear-app** — Path: `brand-inspiration/linear-app/` — Precise product UI, dark restraint, calm density. — includes components, tokens
- **loom** — Path: `brand-inspiration/loom/`
- **lovable** — Path: `brand-inspiration/lovable/`
- **mastercard** — Path: `brand-inspiration/mastercard/`
- **meta** — Path: `brand-inspiration/meta/`
- **minimax** — Path: `brand-inspiration/minimax/`
- **mintlify** — Path: `brand-inspiration/mintlify/`
- **miro** — Path: `brand-inspiration/miro/`
- **mistral-ai** — Path: `brand-inspiration/mistral-ai/`
- **mistral.ai** — Path: `brand-inspiration/mistral.ai/`
- **mongodb** — Path: `brand-inspiration/mongodb/`
- **nike** — Path: `brand-inspiration/nike/` — Bold athletic energy, campaign-driven impact, high contrast.
- **notion** — Path: `brand-inspiration/notion/` — Calm productivity, document-like structure, low visual noise. — includes components, tokens
- **nvidia** — Path: `brand-inspiration/nvidia/`
- **ollama** — Path: `brand-inspiration/ollama/`
- **openai** — Path: `brand-inspiration/openai/` — AI product clarity, calm technical presentation, restrained futurism. — includes components, tokens
- **opencode-ai** — Path: `brand-inspiration/opencode-ai/`
- **opencode.ai** — Path: `brand-inspiration/opencode.ai/`
- **perplexity** — Path: `brand-inspiration/perplexity/`
- **pinterest** — Path: `brand-inspiration/pinterest/`
- **playstation** — Path: `brand-inspiration/playstation/`
- **posthog** — Path: `brand-inspiration/posthog/`
- **raycast** — Path: `brand-inspiration/raycast/`
- **renault** — Path: `brand-inspiration/renault/`
- **replicate** — Path: `brand-inspiration/replicate/`
- **resend** — Path: `brand-inspiration/resend/`
- **revolut** — Path: `brand-inspiration/revolut/`
- **runwayml** — Path: `brand-inspiration/runwayml/`
- **sanity** — Path: `brand-inspiration/sanity/`
- **sentry** — Path: `brand-inspiration/sentry/`
- **shopify** — Path: `brand-inspiration/shopify/` — Commerce enablement, friendly business clarity. — includes components, tokens
- **slack** — Path: `brand-inspiration/slack/` — includes components, tokens
- **spacex** — Path: `brand-inspiration/spacex/`
- **spotify** — Path: `brand-inspiration/spotify/` — Bold media energy, strong color and motion potential. — includes components, tokens
- **starbucks** — Path: `brand-inspiration/starbucks/`
- **stripe** — Path: `brand-inspiration/stripe/` — Polished SaaS clarity, developer/business trust, careful gradients. — includes components, tokens
- **supabase** — Path: `brand-inspiration/supabase/`
- **superhuman** — Path: `brand-inspiration/superhuman/`
- **tesla** — Path: `brand-inspiration/tesla/` — Futuristic product focus, minimal copy, strong hero emphasis.
- **theverge** — Path: `brand-inspiration/theverge/`
- **together-ai** — Path: `brand-inspiration/together-ai/`
- **together.ai** — Path: `brand-inspiration/together.ai/`
- **uber** — Path: `brand-inspiration/uber/` — includes components, tokens
- **vercel** — Path: `brand-inspiration/vercel/` — Developer-focused minimalism, sharp contrast, deployment/product clarity. — includes components, tokens
- **vodafone** — Path: `brand-inspiration/vodafone/`
- **voltagent** — Path: `brand-inspiration/voltagent/`
- **warp** — Path: `brand-inspiration/warp/`
- **webex** — Path: `brand-inspiration/webex/`
- **webflow** — Path: `brand-inspiration/webflow/`
- **wechat** — Path: `brand-inspiration/wechat/` — Social/messaging ecosystem inspiration; use cautiously as high-level reference.
- **wired** — Path: `brand-inspiration/wired/`
- **wise** — Path: `brand-inspiration/wise/`
- **x-ai** — Path: `brand-inspiration/x-ai/`
- **x.ai** — Path: `brand-inspiration/x.ai/`
- **xiaohongshu** — Path: `brand-inspiration/xiaohongshu/` — Content/community inspiration; use as high-level style and content rhythm only.
- **zapier** — Path: `brand-inspiration/zapier/`

---

## Recently Added from open-design

The following references were added or enriched from `nexu-io/open-design`:


### New references

- `brand-inspiration/arc/`
- `style-skills/atelier-zero/`
- `brand-inspiration/canva/`
- `brand-inspiration/cisco/`
- `style-skills/default/`
- `brand-inspiration/discord/`
- `brand-inspiration/duolingo/`
- `brand-inspiration/github/`
- `style-skills/hud/`
- `brand-inspiration/huggingface/`
- `brand-inspiration/kami/`
- `brand-inspiration/linear-app/`
- `brand-inspiration/loom/`
- `style-skills/mission-control/`
- `brand-inspiration/mistral-ai/`
- `brand-inspiration/openai/`
- `brand-inspiration/opencode-ai/`
- `brand-inspiration/perplexity/`
- `brand-inspiration/together-ai/`
- `style-skills/totality-festival/`
- `style-skills/trading-terminal/`
- `style-skills/urdu/`
- `style-skills/warm-editorial/`
- `brand-inspiration/webex/`
- `brand-inspiration/wechat/`
- `brand-inspiration/x-ai/`
- `brand-inspiration/xiaohongshu/`

### Enriched with components/tokens

- `brand-inspiration/figma/components.html`
- `brand-inspiration/figma/tokens.css`
- `brand-inspiration/apple/components.html`
- `brand-inspiration/apple/tokens.css`
- `brand-inspiration/notion/components.html`
- `brand-inspiration/notion/tokens.css`
- `brand-inspiration/uber/components.html`
- `brand-inspiration/uber/tokens.css`
- `brand-inspiration/stripe/components.html`
- `brand-inspiration/stripe/tokens.css`
- `brand-inspiration/vercel/components.html`
- `brand-inspiration/vercel/tokens.css`
- `brand-inspiration/shopify/components.html`
- `brand-inspiration/shopify/tokens.css`
- `brand-inspiration/spotify/components.html`
- `brand-inspiration/spotify/tokens.css`
- `brand-inspiration/airbnb/components.html`
- `brand-inspiration/airbnb/tokens.css`
- `brand-inspiration/slack/components.html`
- `brand-inspiration/slack/tokens.css`
- `brand-inspiration/cursor/components.html`
- `brand-inspiration/cursor/tokens.css`
