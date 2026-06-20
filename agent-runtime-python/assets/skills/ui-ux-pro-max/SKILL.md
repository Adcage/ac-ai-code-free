---
name: ui-ux-pro-max
description: |
  Data-driven UI/UX design system skill with BM25 search engine. Contains 67
  styles, 96 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart
  types across 13 technology stacks. Use for any frontend task that needs
  professional design direction — landing pages, dashboards, SaaS apps,
  e-commerce, portfolios, or any UI that should look polished rather than
  generic.
---

# ui-ux-pro-max

Use this skill when the user asks to build or improve a frontend interface and you need professional design direction backed by data, not guesswork.

The core of this skill is a **BM25 search engine** over curated CSV databases. You call it via `run_command` to get style, color, typography, layout, and UX recommendations with reasoning.

## Resource map

```
ui-ux-pro-max/
├── SKILL.md                ← you're reading this
├── scripts/
│   ├── search.py           ← CLI entry point (main command)
│   ├── core.py             ← BM25 engine + domain search
│   └── design_system.py    ← Design system generator
└── data/
    ├── styles.csv          ← 67 UI styles with effects, keywords, CSS vars
    ├── colors.csv          ← 96 color palettes by product type
    ├── typography.csv      ← 57 font pairings with Google Fonts URLs
    ├── ux-guidelines.csv   ← 99 UX best practices with do/don't/code
    ├── products.csv        ← Product type → style/landing recommendations
    ├── landing.csv         ← Landing page patterns + conversion strategies
    ├── charts.csv          ← 25 chart types with library recommendations
    ├── icons.csv           ← Icon library recommendations by category
    ├── ui-reasoning.csv    ← Reasoning rules for design decisions
    ├── web-interface.csv   ← Web accessibility + interaction guidelines
    ├── react-performance.csv ← React/Next.js performance patterns
    └── stacks/
        ├── vue.csv           ← Vue Composition API + Pinia guidelines
        ├── react.csv         ← React hooks + performance guidelines
        ├── html-tailwind.csv ← Tailwind utilities + responsive + a11y
        ├── nextjs.csv        ← SSR + routing + images
        ├── nuxtjs.csv        ← Nuxt auto-imports + SSR
        ├── nuxt-ui.csv       ← Nuxt UI components
        ├── svelte.csv        ← Svelte runes + stores
        ├── astro.csv         ← Astro islands + content
        ├── shadcn.csv        ← shadcn/ui components + theming
        ├── swiftui.csv       ← SwiftUI views + animation
        ├── react-native.csv  ← RN components + navigation
        ├── flutter.csv       ← Flutter widgets + theming
        └── jetpack-compose.csv ← Compose modifiers + state
```

## Workflow

### Step 1 — Analyze user requirements

Extract from the user's request:
- **Product type**: SaaS, e-commerce, portfolio, dashboard, landing page, etc.
- **Style keywords**: minimal, playful, professional, elegant, dark mode, etc.
- **Industry**: healthcare, fintech, gaming, education, beauty, etc.
- **Stack**: Vue, React, Next.js, or default to the project's framework

### Step 2 — Generate design system (REQUIRED, always do this first)

Run the search script to get a comprehensive design system recommendation:

```
python {skill_dir}/scripts/search.py "<product_type> <industry> <keywords>" --design-system -p "Project Name"
```

Example:
```
python {skill_dir}/scripts/search.py "SaaS dashboard analytics professional" --design-system -p "DataPulse"
```

This command:
1. Searches 5 domains in parallel (product, style, color, landing, typography)
2. Applies reasoning rules from `ui-reasoning.csv` to select best matches
3. Returns complete design system: pattern, style, colors, typography, effects
4. Includes anti-patterns to avoid

**Important**: `{skill_dir}` is the absolute path to this skill's directory. It will be provided in the system prompt after you select this skill. Use it directly in the command.

### Step 3 — Supplement with detailed searches (as needed)

After getting the design system, use domain searches for additional details:

```
python {skill_dir}/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

| Need | Domain | Example |
|------|--------|---------|
| More style options | `style` | `--domain style "glassmorphism dark"` |
| Chart recommendations | `chart` | `--domain chart "real-time dashboard"` |
| UX best practices | `ux` | `--domain ux "animation accessibility"` |
| Alternative fonts | `typography` | `--domain typography "elegant luxury"` |
| Landing structure | `landing` | `--domain landing "hero social-proof"` |
| Icon choices | `icons` | `--domain icons "navigation action"` |
| Product patterns | `product` | `--domain product "healthcare SaaS"` |
| Color palettes | `color` | `--domain color "fintech crypto"` |
| Web a11y | `web` | `--domain web "aria focus keyboard"` |
| React perf | `react` | `--domain react "suspense memo rerender"` |

### Step 4 — Stack guidelines

Get implementation-specific best practices for the target framework:

```
python {skill_dir}/scripts/search.py "<keyword>" --stack <stack_name>
```

Available stacks: `html-tailwind`, `react`, `nextjs`, `vue`, `nuxtjs`, `nuxt-ui`, `svelte`, `astro`, `shadcn`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`

For Vue projects, always run:
```
python {skill_dir}/scripts/search.py "layout responsive form" --stack vue
```

### Step 5 — Build the interface

Synthesize the design system + detailed search results and implement:
- Use the recommended color palette as CSS custom properties
- Apply the typography pairing (heading + body fonts)
- Follow the landing page pattern section order
- Respect the anti-patterns list
- Apply stack-specific guidelines

Use `write_file` to write real project files. Do not wrap output in `<artifact>` tags.

## Hard rules

- **No emoji icons** — Use SVG icons (Heroicons, Lucide, Simple Icons). Never use emojis as UI icons.
- **cursor-pointer on all clickable elements** — Cards, buttons, links, any interactive element.
- **Smooth transitions** — Use `transition-colors duration-200` or equivalent. No instant state changes. No transitions over 500ms.
- **Light mode contrast** — Text must be at least 4.5:1 contrast ratio. Never use `#94A3B8` (slate-400) for body text in light mode.
- **Glass card light mode** — Use `bg-white/80` or higher opacity. Never `bg-white/10` in light mode.
- **Single accent color** — Used at most twice per screen (eyebrow + primary CTA is the default budget).
- **Stable hover states** — Use color/opacity transitions. Never use scale transforms that shift layout.
- **Floating navbar spacing** — Add `top-4 left-4 right-4` spacing. Never stick directly to viewport edges.
- **Responsive** — Must work at 375px, 768px, 1024px, 1440px. No horizontal scroll on mobile.
- **prefers-reduced-motion** — Respect this media query for accessibility.

## Pre-delivery checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] Brand logos are correct (verified from Simple Icons)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states provide clear visual feedback
- [ ] Transitions are smooth (150-300ms)
- [ ] Light mode text has sufficient contrast (4.5:1 minimum)
- [ ] Glass/transparent elements visible in light mode
- [ ] Borders visible in both light and dark modes
- [ ] No content hidden behind fixed navbars
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color is not the only indicator
- [ ] `prefers-reduced-motion` respected
- [ ] Focus states visible for keyboard navigation
