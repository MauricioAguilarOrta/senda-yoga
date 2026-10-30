---
name: yoga-brand
description: Apply Senda Yoga's warm, editorial, contemporary brand identity when designing or changing user-facing interfaces, components, layouts, and interaction states.
---

# Senda Yoga — Brand Design Skill

## Purpose and usage

Use this skill when creating or modifying Senda Yoga interfaces. Combine **the earthy colors of Tierra Serena**, **the clean contemporary lowercase wordmark of Equilibrio Moderno**, and **the editorial typography and composition of Esencia Artesanal**.

The application should feel like a calm, welcoming boutique yoga studio while remaining precise and efficient for attendance management. This skill is about presentation; the feature specification governs business logic.

## 1. Brand identity

- Personality: warm, calm, trustworthy, contemporary, personal, and subtly artisanal.
- Avoid generic fitness dashboards, heavy green fills, bright gradients, oversized hero imagery on operational screens, and decorative clutter.
- Use the wordmark **senda** in lowercase in a clean, contemporary sans-serif style, with **YOGA STUDIO** in small, widely tracked capitals below it.
- The wordmark should remain typographically distinct from editorial headings. If no official image/SVG asset exists, render a restrained text wordmark rather than inventing a complex logo. Do not claim that a typographic fallback is the official logo.

## 2. Color tokens

Define these tokens centrally, reusing them consistently:

| Token | Value | Role |
|---|---|---|
| `--color-background` | `#F8F4EE` | Warm sand page background |
| `--color-surface` | `#FFFDFC` | Warm white cards and dialogs |
| `--color-sage` | `#A7B89F` | Subtle supporting accents |
| `--color-terracotta` | `#C97F63` | Visual identity and progress |
| `--color-mocha` | `#7A5E4D` | Warm secondary accents |
| `--color-charcoal` | `#2E2E2B` | Main text and dark controls |
| `--color-border` | `#E8DED2` | Delicate boundaries |
| `--color-muted` | `#6B6863` | Secondary text |

- Let sand and warm-white surfaces dominate; use terracotta deliberately, not everywhere.
- Most functional text should be charcoal.
- Avoid white text on the supplied terracotta without verifying contrast; select a darker contrast-compliant action variant or dark text as appropriate.
- Provide distinct success, warning, and error states with text and icons; status must never rely on color alone.

## 3. Typography

- **Playfair Display:** editorial headings, greetings, selected branded statements; never dense tables, forms, labels, or operational status.
- **Lato:** body copy, numerical balances, buttons, navigation, form labels, lists, error messages, and data views.
- Responsive heading scale: desktop H1 36px, H2 28px, H3 22px; reduce as needed on mobile.
- Body 16px; labels 14px; button text 15–16px; secondary information 14px (smaller only if comfortably readable).
- Use tabular numbers where available for package counts. Provide sensible fallback fonts if web fonts cannot load.

## 4. Layout and rhythm

- Mobile first; retain adequate margins, especially on compact displays.
- Use an 8px spacing scale: 8px tight gaps, 16px common gaps, 20–24px card padding, 24–32px section spacing, 40–48px for larger editorial separations.
- Warm-white cards with 16–24px corner radii, subtle border, and almost imperceptible shadow when helpful.
- Editorial headings may be slightly asymmetric with generous whitespace and an occasional botanical accent; forms, numbers, operational controls, and data lists must align consistently.
- Student views: greeting → total available classes → individual packages/progress → history access.
- Instructor views: session selection → student search/list → remaining balance → confirm attendance → visible feedback.
- Administrator views: package/student management → sessions → attendance history → correction controls.
- Mobile bottom navigation is appropriate for student screens, but only include implemented destinations. Use practical navigation for administrative flows.

## 5. Buttons and interaction

- Primary actions: warm terracotta visual language with **verified text contrast**, subtly organic but regular rounded rectangle (~14–18px radius), at least 44×44 CSS px touch target, Lato medium weight, and little or no shadow.
- Secondary actions: warm-white or transparent surface, thin mocha or charcoal border, dark text, same radius family.
- Tertiary actions: restrained text treatment.
- Consistent hover, focus-visible, loading, disabled, success, and error states.
- Do **not** use brush-stroke silhouettes or irregular hitboxes for attendance confirmations and other critical actions.
- Prefer one obvious primary action per screen, with short Spanish labels.

## 6. Signature components

### Package card
Show package identity, initial and remaining class counts, progress, and access to relevant attendance history. The numeric balance must be legible independently of color or graphics. Do not assume packages always contain ten classes.

### Progress
Use a circular or segmented progress treatment accented with terracotta, supported by explicit labels such as "8 de 10 clases". Handle arbitrary positive package sizes.

### Organic detail
Sparse line-art botanical and abstract natural motifs may decorate welcome headers, noncritical card corners, and empty states. Never put patterns behind balances, forms, navigation, or critical buttons.

## 7. Language and accessible use

- All user-facing copy is **Spanish**, warm and concise: "Hola, Mariana", "8 clases disponibles", "Registrar asistencia", "Asistencia confirmada", "Este registro fue corregido".
- Avoid excessive punctuation, technical jargon, and vague errors such as "Error" without an explanation.
- Meet WCAG 2.2 AA principles where applicable: text contrast, visible keyboard focus, labeled form controls, keyboard interaction, readable mobile layout, explanatory error states, alternatives for meaningful imagery, and respect for reduced-motion preferences.
- Never sacrifice readability or task efficiency for decoration.

## 8. Agent procedure

1. Read `AGENTS.md` and the current feature spec.
2. Identify the role, task, and critical information in each screen.
3. Reuse color tokens, Playfair/Lato typography, spacing, and component patterns.
4. Build mobile-first responsive states, including loading, empty, success, error, and disabled.
5. Add organic artwork only where it supports the brand without obscuring information.
6. Test responsive layout, color contrast, keyboard access, and functional clarity.
7. Confirm visuals faithfully represent the actual persisted application data.
8. Report any deviations and why they were necessary.

## 9. Quality checklist

- [ ] Earthy palette applied consistently through tokens.
- [ ] Clean lowercase senda wordmark, with YOGA STUDIO descriptor.
- [ ] Playfair Display used for editorial headings; Lato for functional content.
- [ ] Warm-white cards and consistent spacing and corner radii.
- [ ] Accessible action contrast and visible focus.
- [ ] Clear balances and package-level progress.
- [ ] Spanish copy; responsive mobile screens.
- [ ] Artisanal details are subtle and never obscure controls.
- [ ] No dead navigation links or misleading active controls.
- [ ] No business rules changed for design reasons.

## 10. Scope boundary

This skill never overrides the spec on package quantities, deduction order, session validation, permissions, concurrency, persistence, or reversals.
