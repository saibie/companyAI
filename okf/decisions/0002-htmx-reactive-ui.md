---
type: decision
title: "ADR 0002: Django Templates + HTMX over Heavy SPA Frameworks"
description: Architectural decision adopting Django templates with HTMX for real-time reactivity without JavaScript build toolchains.
updated_at: 2026-09-23
status: accepted
tags:
  - adr
  - htmx
  - frontend
  - django-templates
---

# ⚖️ ADR 0002: Django Templates + HTMX over Heavy SPA Frameworks

## Context
The CEO dashboard requires real-time task polling, dynamic status transitions, agent tree visualizations, and interactive approval flows. Traditional Single Page Applications (React, Vue, Next.js) introduce complex build pipelines (Node, npm, bundlers), state duplication, and REST API boilerplate.

## Decision
Adopt **Django Templates** enhanced with **HTMX** (`django-htmx`):
- HTML partials rendered on the server and swapped into the DOM via `hx-get`, `hx-post`, `hx-swap="outerHTML"`.
- Real-time polling via `hx-trigger="every 3s"`.
- No Node.js build step or separate frontend dev server required.

## Consequences
- **Positive**: Single unified Python codebase, direct access to Django ORM inside templates, minimal client-side dependencies, zero JavaScript bundler overhead.
- **Negative**: Advanced complex client-side Canvas or 3D animations require custom vanilla JavaScript.
