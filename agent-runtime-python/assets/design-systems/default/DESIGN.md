# Default Design System

This design system defines the baseline visual rules for generated Vue projects. All generated pages must follow these rules to ensure visual consistency and product-quality output.

## Color Rules

- Use `--color-primary` (#1677ff) as the primary action color for buttons, links, active states, and key interactive elements.
- Use `--color-success` (#22c55e) for positive feedback, confirmations, and completed states.
- Use `--color-warning` (#f59e0b) for caution indicators and pending states.
- Use `--color-danger` (#ef4444) for errors, destructive actions, and critical alerts.
- Use `--color-text` (#111827) for primary body text.
- Use `--color-muted` (#6b7280) for secondary text, labels, and placeholder content.
- Use `--color-surface` (#ffffff) for card backgrounds and content containers.
- Use `--color-page` (#f5f7fb) for page-level backgrounds.
- Do not introduce arbitrary colors outside this palette unless the user explicitly requests it.
- Maintain sufficient contrast between text and background colors (minimum 4.5:1 for normal text).

## Typography Rules

- Use a system font stack as the base font family: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`.
- Monospace code should use `"SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace`.
- Page title: 24px, font-weight 600.
- Section title: 20px, font-weight 600.
- Card title: 16px, font-weight 600.
- Body text: 14px, font-weight 400, line-height 1.6.
- Small/auxiliary text: 12px, font-weight 400.
- Do not use font sizes below 12px for any readable text.

## Spacing Rules

- Base spacing unit: 4px.
- Use multiples of 4px for all spacing values (4, 8, 12, 16, 20, 24, 32, 40, 48, 64).
- `--space-md` (16px) is the default content padding for cards and containers.
- Page-level padding: 24px.
- Gap between sibling cards: 16px.
- Form item spacing: 24px vertical gap between items.
- Do not use arbitrary spacing values like 13px, 7px, or 15px.

## Card Rules

- Card background: `--color-surface` (#ffffff).
- Card border-radius: `--radius-card` (8px).
- Card padding: 16px-24px.
- Cards on a dashboard should have consistent height within the same row, or use stretch alignment.
- Card titles should be concise, using real business text, never "Card 1" or "Metric A".
- Card content should be substantive, not placeholder text.
- Use subtle box-shadow for card elevation: `0 1px 3px rgba(0,0,0,0.08)`.

## Form Rules

- Form labels must be present for all inputs, either as visible labels or `aria-label`.
- Input fields should have clear focus states using `--color-primary`.
- Required fields should be indicated visually.
- Error messages should appear near the relevant field, not in a global alert.
- Form layout should use consistent alignment and spacing.

## Button Rules

- Primary buttons: `--color-primary` background, white text.
- Secondary buttons: transparent or `--color-page` background, `--color-text` text, 1px `--color-primary` border.
- Danger buttons: `--color-danger` background, white text.
- Button border-radius: 6px.
- Button padding: 8px 16px for medium size.
- Disabled buttons should have reduced opacity (0.5) and no pointer events.
- Button text should be action-oriented and concise.

## Table Rules

- Table header: `--color-page` background, `--color-muted` text, 12px font-weight 600.
- Table rows: alternating or consistent `--color-surface` background.
- Row hover: subtle background change using `--color-page`.
- Column alignment: text left, numbers right.
- Table should handle empty states gracefully with a centered message.
- Table pagination should be present when rows exceed 10.

## Visual Quality Constraints for Vue Projects

- Generated pages must look like a real product, not a wireframe or prototype.
- Do not leave empty sections, placeholder cards, or "Lorem ipsum" text.
- All interactive elements (buttons, links, tabs) must have hover and active states.
- Use real Chinese business text for labels, descriptions, and sample data.
- Do not use "Metric A", "Card 1", "Item 1", or similar placeholder labels.
- Layout should be responsive-friendly with proper flex or grid usage.
- Avoid inline styles when CSS classes or design tokens are available.
- SVG icons should be sized consistently (16px or 20px) and use `currentColor`.
