---
name: web-prototype
description: General-purpose desktop web prototype for single-page landing, marketing
  page, homepage, docs index, or any general-purpose web page that doesn't
  match a more specific skill.
---

# Web Prototype Skill

Produce a real HTML prototype using the bundled references and design system tokens — **not** by writing CSS from scratch. Use file tools to write the actual project files under the workspace.

## Resource map

```
web-prototype/
├── SKILL.md                ← you're reading this
├── references/
│   ├── layouts.md          ← paste-ready section skeletons
│   └── checklist.md        ← P0/P1/P2 self-review
```

## Workflow

### Step 0 — Pre-flight (do this once before writing anything)

1. **Read `references/layouts.md`** so you know which section skeletons exist. Don't write a section type that isn't covered — pick the closest layout and adapt.
2. **Read the active DESIGN.md** (already injected into your system prompt). Map its colors to CSS custom properties; don't introduce new tokens.

### Step 1 — Prepare the project files

Use file tools (`write_file`) to create the project files under the workspace. Do not emit content wrapped in `<artifact>` tags.

- For `single_file` mode: write one complete `index.html` with inline `<style>` and `<script>`.
- For `multi_file` mode: write `index.html`, `style.css`, and `script.js` in the same directory.

Replace CSS custom properties with the active design system's tokens. Replace the page `<title>` and any topnav brand.

### Step 2 — Plan the section list

**Pick layouts before writing copy.** Default rhythms (from `layouts.md`):

| Page kind | Default rhythm |
|---|---|
| Landing | 1 hero → 3 features → 4 stats *or* 5 quote → custom split → 6 cta |
| Marketing / editorial | 1 hero-center → 7 log list → 6 cta |
| Pricing | 1 hero-center → 8 comparison table → 6 cta |
| Docs index | 1 hero-center → 7 log list (sections of docs) → 6 cta |

State the chosen list in one sentence to the user *before* writing — they can redirect cheaply now and not after 200 lines of HTML.

### Step 3 — Paste and fill

For each chosen layout, copy the `<section>` block from `layouts.md` into your HTML. Replace bracketed `[REPLACE]` strings with real, specific copy from the user's brief. **No filler** — if a slot is empty, the section is the wrong choice; pick a different layout.

### Step 4 — Self-check

Run through `references/checklist.md` top to bottom. Every P0 item must pass before you move on. P1 items should pass; P2 are bonus.

### Step 5 — Write the files

Use `write_file` to write the final HTML/CSS/JS. The runtime will collect an artifact manifest after tool execution. One sentence before writing, describing what's being created.

## Hard rules

- **Single accent, used at most twice per screen.** Eyebrow + primary CTA is the default budget.
- **Display font is serif** (Iowan Old Style / Charter / Georgia). Sans for body. Mono for numerics, captions, eyebrows.
- **Image placeholders, not external URLs.** Use placeholder markup — never link to a stock photo CDN.
- **Mobile reflow already works** via media queries. Don't break it by adding fixed widths.
- **`data-od-id` on every `<section>`** so comment mode can target it.

## Output contract

Use file tools (`write_file`) to write real project files under the workspace.

- For `single_file` output mode: write one complete `index.html` with inline `<style>` and `<script>`.
- For `multi_file` output mode: write `index.html`, `style.css`, and `script.js`.
- Do not wrap output in `<artifact>` tags.
- Do not write another root HTML draft beside the canonical files for the same generation turn.
