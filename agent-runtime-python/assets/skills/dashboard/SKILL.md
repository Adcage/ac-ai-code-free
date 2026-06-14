---
name: dashboard
description: Dashboard screen.
triggers:
  - dashboard
  - 后台
  - 看板
od:
  mode: prototype
  platform: desktop
  scenario: operations
  preview:
    type: html
    entry: index.html
  design_system:
    requires: true
    sections: [color, typography, layout]
  craft:
    requires: [state-coverage, accessibility-baseline]
---

# Dashboard Skill

Build a dashboard with real data and complete functionality.

## Requirements

- Generate Vue project files using write_file tool
- Use real Chinese business text, not placeholder content
- Do not use placeholder metrics like "Metric A" or "Card 1"
- Use tools to write actual files to workspace
- Include real chart data and table data
- Ensure all interactive elements are functional
