---
id: state-coverage
name: State Coverage
description: Ensure pages cover loading, empty, and error states.
appliesTo: ["vue_project", "multi-file"]
priority: 30
---

# State Coverage

- Pages should include loading, empty, and error states or reasonable static alternatives.
- Data cards must not be all placeholders.
- Lists should show empty state when no data is available.
- Loading indicators should be present for async operations.
- Error states should provide actionable feedback.
