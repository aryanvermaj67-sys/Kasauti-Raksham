---
name: Kasauti Verification System
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fc'
  on-secondary-container: '#57657a'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#00201d'
  on-tertiary-container: '#389189'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fc'
  secondary-fixed-dim: '#b9c7df'
  on-secondary-fixed: '#0d1c2e'
  on-secondary-fixed-variant: '#3a485b'
  tertiary-fixed: '#9cf2e8'
  tertiary-fixed-dim: '#80d5cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#00504a'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-lg-medium:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-lg-bold:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  legal-disclaimer:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-tablet: 1.5rem
  gutter-desktop: 2rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system provides an institutional, zero-ambiguity framework for financial claim audit and verification inside retail and wealth banking platforms. Built on principles of legal and evidentiary neutrality, the design avoids emotional flourishes, celebratory badges, gamification, and panic-inducing alerts. It delivers an objective, court-record level of visual restraint.

### Aesthetic Foundation
- **Institutional Realism & Neutrality**: Interfaces reflect auditing rigor. Surfaces are flat, structured, and low-sheen. Contrast ratios exceed standard compliance to guarantee immediate legibility across varied device qualities and ambient conditions.
- **De-escalation & Objectivity**: Contradictions, discrepancies, and matches are rendered as factual comparisons rather than praise or punitive errors. The interface serves as an impartial verifier between third-party marketing assertions and official regulatory ledgers.
- **Bilingual Functional Parity**: Engineered from the ground up for simultaneous Latin and Devanagari script integration, ensuring structural balance, uniform baselines, and uncompromising readability across English and Hindi strings.

## Colors

The palette is anchored in an authoritative slate navy, structured neutrals, and strictly functional verification tiers. Color is never used as the sole conveyor of information; every status state mandates a compound presentation of an icon, explicit institutional text, and high-contrast structural borders.

### Primary & Core Neutrals
- **Primary Canvas & Text (`#0F172A`, `#1E293B`)**: Used for absolute legibility in primary headers, master record containers, and actionable interactive controls.
- **Surface Neutrals (`#F8FAFC`, `#F1F5F9`, `#E2E8F0`)**: Provide crisp layer differentiation without relying on blur or heavy dropped shadows.
- **Subdued Accents & Metadata (`#475569`, `#94A3B8`)**: Designated for field borders, secondary labels, metadata tags, and non-actionable structure lines.

### Verification Status Tokens
- **Contradiction State**:
  - Surface: `#FEF2F2`
  - Border: `#F87171`
  - Text & Glyph: `#991B1B`
  - Requirement: Always accompanied by the alert triangle icon and the label `CONTRADICTS THE RECORD`. Never use pure crimson fills without structural borders.
- **Verified Match State**:
  - Surface: `#F0FDFA`
  - Border: `#99F6E4`
  - Text & Glyph: `#0F766E`
  - Requirement: A sober, subdued slate-teal presentation. Always accompanied by the balance/equality check icon and the explicit label `MATCHES THE RECORD`. Never use celebratory green or safety seals.
- **Indeterminate / Unverified State**:
  - Surface: `#F8FAFC`
  - Border: `#CBD5E1`
  - Text & Glyph: `#475569`
  - Requirement: Accompanied by the search/query glyph and the label `NO RECORD FOUND`.

### Contextual Claims Differentiation
- **Claimed Assertion (`#F1F5F9`)**: Neutral grey container with clear quote marks indicating unverified external content (`What the claim/ad says`).
- **Verified Banking Record (`#0F172A` tint / `#F8FAFC` slate-lined base)**: Authoritative slate container representing system-of-record data (`What your official record says`).

## Typography

The typography uses Inter across headlines, body copy, and UI metadata, with runtime fallback to Noto Sans Devanagari to preserve optical proportion and line heights.

### Baseline Rules & Accessibility
- **Minimum Base Size**: Body copy never dips below `16px` in standard operations. Sub-labels and metadata may scale down to `12px` only for secondary legal timestamps and audit hash strings.
- **Large Text Accessibility Mode**: When activated, base body text elevates from `16px` to `19px` (line-height: `28px`), and labels scale from `14px` to `16px`. Structural layouts expand dynamically to accommodate localized Devanagari expansion (which averages 15–20% greater horizontal width).
- **Tabular Numerals**: Numerical amounts, interest calculations, claim percentages, and date stamps must consistently implement `font-variant-numeric: tabular-nums` to enable scan-verification across data tables.

## Layout & Spacing

Layouts follow a structured grid system engineered to convey stability and sequential audit logic. 

### Grid & Breakpoints
- **Mobile (`< 640px`)**: Single column fluid container with a minimum `16px` horizontal margin. All critical interactive targets adhere to a mandatory `44px` minimum touch height.
- **Tablet (`640px - 1024px`)**: 6-column grid with `24px` margins and `16px` gutters. Used primarily for comparison viewports where 'Claimed Statement' and 'Official Record' are placed in side-by-side verification panels.
- **Desktop / Auditing Presenter (`> 1024px`)**: 12-column grid with `32px` margins and `24px` gutters. Max container width capped at `1280px` to maintain optimal line-lengths during evidentiary review.

### Spacing Strategy
- Spacing rhythm follows strict 4px/8px multiples (`space-xs` = 4px, `space-sm` = 8px, `space-md` = 16px, `space-lg` = 24px, `space-xl` = 32px).
- Verification comparison pairs must maintain equal internal padding (`space-md`) to ensure neither the claim nor the verified ledger appears visually prioritized.

## Elevation & Depth

To maintain institutional authority and compliance clarity, this design system avoids heavy shadows, saturated colored blurs, and skeuomorphic gradients. Depth is established through tonal containment and crisp, low-contrast outlines.

### Depth Hierarchy
1. **Canvas Surface (Level 0)**: `#F8FAFC`. The foundational backdrop for forms, verification streams, and audit histories.
2. **Structural Card Surface (Level 1)**: Pure `#FFFFFF` surface enclosed with a 1px solid border (`#E2E8F0`). Flat elevation, zero drop shadow.
3. **Elevated Overlays & Bottom Sheets (Level 2)**: Used for granular ledger proof modals and modal bottom sheets. Surfaces are pure `#FFFFFF` resting on a subtle, ultra-diffused structural anchor: `0 4px 12px 0 rgba(15, 23, 42, 0.08)`. Requires a 1px border (`#CBD5E1`) and a high-contrast backing backdrop (`#0F172A` at 40% opacity).
4. **Watermark / Inactive Layer**: Synthetic test and presentation data badges are superimposed at `rgba(15, 23, 42, 0.04)` rotated at -12 degrees to ensure non-interference with underlying verification typography.

## Shapes

The design uses soft, structural corner radiuses to reinforce banking stability, avoiding rounded pill aesthetics that evoke casual consumer apps.

- **Base Components (Level 1)**: All interactive buttons, verification cards, form fields, and status banners use a subtle `0.25rem` (4px) corner radius.
- **Containers & Sheets (`rounded-lg`)**: Modal bottom sheets and comparison panels employ `0.5rem` (8px) on outer containers. Top edges of mobile presentation sheets utilize `0.5rem` (8px).
- **Prohibited Geometry**: Never use circular pills (`rounded-full` or radius > 8px) for buttons, audit labels, or status indicators. All borders must present clean, architectural terminations.

## Components

### Buttons
- **Primary Action**: Solid `#0F172A` background, `#FFFFFF` text, 4px border radius. Minimum height of 48px on touch viewports. Hover state transitions to `#1E293B`.
- **Secondary Action**: Border of 1px solid `#CBD5E1`, background `#FFFFFF`, text `#0F172A`. Minimum height 48px.
- **Destructive / Flag Claim**: Border 1px solid `#F87171`, background `#FEF2F2`, text `#991B1B`. Accompanied by flag/dispute icon.

### Status Banners & Chips
- Status indicators must be rendered as rectangular, 1px bordered elements with a strict 4px radius.
- Must include a `16px` icon on the left, an uppercase bold label (`CONTRADICTS THE RECORD`, `MATCHES THE RECORD`, `NO RECORD FOUND`), and localized translation below if the bilingual mode is active.
- Pure color dots or unaccompanied status labels are strictly forbidden.

### Verification Comparison Cards
- **External Claim Container**:
  - Background: `#F1F5F9`.
  - Border: 1px dashed `#CBD5E1`.
  - Visual Cue: Quote icon with header `CLAIMED ASSERTION`.
- **Official Ledger Container**:
  - Background: `#FFFFFF`.
  - Border: 1.5px solid `#0F172A`.
  - Visual Cue: Institutional bank seal or ledger glyph with header `CENTRAL REPOSITORY RECORD`.

### Modal Bottom Sheets
- Deployed for granular audit-trail inspections.
- Features a centered 32px x 4px grab handle in `#CBD5E1`.
- Retains safe margins on presentation screens, supporting instant swipe-to-dismiss and an explicit top-right institutional `Close` button.

### Form Inputs & Checks
- **Input Fields**: 1px solid border (`#CBD5E1`), transitioning to 1.5px `#0F172A` on focus. Height 48px, minimum font size 16px to prevent automated zoom on mobile devices.
- **Checkboxes & Radios**: Strictly 18px x 18px with 2px borders, utilizing high-contrast `#0F172A` fills when active.

### Synthetic Data Watermark Badges
- Non-production or simulated claim audits must overlay an unmissable, repeating diagonal watermarked tag (`SYNTHETIC DATA — FOR TESTING ONLY`) rendered in uppercase 12px monospaced typography with a contrast ratio calibrated to remain readable without obstructing operational data.