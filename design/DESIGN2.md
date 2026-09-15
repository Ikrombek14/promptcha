---
name: Editorial Document Workspace
colors:
  surface: '#faf8fe'
  surface-dim: '#dad9df'
  surface-bright: '#faf8fe'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f8'
  surface-container: '#efedf3'
  surface-container-high: '#e9e7ed'
  surface-container-highest: '#e3e2e7'
  on-surface: '#1a1b1f'
  on-surface-variant: '#434655'
  inverse-surface: '#2f3034'
  inverse-on-surface: '#f1f0f6'
  outline: '#747686'
  outline-variant: '#c4c5d7'
  surface-tint: '#2151da'
  primary: '#0037b0'
  on-primary: '#ffffff'
  primary-container: '#1d4ed8'
  on-primary-container: '#cad3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#5a5e69'
  on-secondary: '#ffffff'
  secondary-container: '#dee2ef'
  on-secondary-container: '#60646f'
  tertiary: '#7f2500'
  on-tertiary: '#ffffff'
  tertiary-container: '#a73400'
  on-tertiary-container: '#ffc9b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001551'
  on-primary-fixed-variant: '#0039b5'
  secondary-fixed: '#dee2ef'
  secondary-fixed-dim: '#c2c6d3'
  on-secondary-fixed: '#171c25'
  on-secondary-fixed-variant: '#424751'
  tertiary-fixed: '#ffdbcf'
  tertiary-fixed-dim: '#ffb59c'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832700'
  background: '#faf8fe'
  on-background: '#1a1b1f'
  surface-variant: '#e3e2e7'
typography:
  headline-xl:
    fontFamily: Instrument Serif
    fontSize: 44px
    fontWeight: '400'
    lineHeight: 52px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Instrument Serif
    fontSize: 32px
    fontWeight: '400'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Instrument Serif
    fontSize: 32px
    fontWeight: '400'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Instrument Serif
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 32px
  headline-sm:
    fontFamily: Instrument Serif
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28.8px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 25.6px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22.4px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
---

## Brand & Style

This design system embodies an editorial, paper-and-ink sensibility engineered for deliberate, focused writing and document curation. The audience comprises writers, researchers, editors, and knowledge workers who require cognitive calm, strict typographical hierarchy, and structural clarity over ornamental distraction.

Drawing heavily from the traditions of physical print publishing and contemporary Swiss functionalism, the visual tone is quiet, tactile, and authoritative. Visual noise is systematically eliminated: no gradients, no synthetic blurs, no ambient glows, and no decorative drop shadows. Visual weight is articulated purely through crisp ruled lines, structural whitespace, and precise typographic contrast. Every interactive element feels physical and deliberate, establishing an environment where words and data remain the sole focal point.

## Colors

The palette operates under strict discipline to maintain an authentic paper-and-ink reading condition. High-chroma accents are restrained to functional markers and active states.

- **Canvas Background (`#F7F6F2`)**: Warm, unbleached paper stock base that eliminates glare during long reading sessions.
- **Surface (`#FFFFFF`)**: Pure sheet white reserved for active document sheets, cards, floating menus, and input fields.
- **Structural Border (`#E4E2DC`)**: Neutral parchment rule used for 1px layout boundaries, structural dividers, and component perimeters.
- **Text / Ink (`#17181C`)**: Deep lamp-black pigment offering high-contrast, effortless legibility without the harshness of pure black.
- **Muted Ink (`#6B6E76`)**: Mid-tone slate for metadata, captions, inactive icons, and placeholder copy.
- **Accent Cobalt (`#1D4ED8`)**: Strictly reserved for three locations: primary action buttons, 2px focus indicators, and 2px left-hand callout rules. It is never used decoratively or for secondary links.
- **Accent Soft (`#EEF2FF`)**: Subtle tinted wash applied strictly to active selections, highlight states, and code callout backdrops.

## Typography

The typographic hierarchy balances literary authority with functional precision:

- **Instrument Serif** anchors the editorial personality. It is applied to article titles, section leads, and key modal headers. Headings should be set in regular weight (`400`) to let the letterforms' natural contrast and rhythm carry structure without heavy boldness.
- **Inter** handles document reading, UI microcopy, and navigation. Standard body text never drops below 16px with a strict minimum line-height of 1.6 (`25.6px`) to ensure reading comfort comparable to printed journals.
- **JetBrains Mono** is specified at 15px with proportional leading for prompt input/output blocks, technical tokens, timestamps, and raw data outputs.

## Layout & Spacing

The layout is built upon a rigid 4px/8px structural increment. Spacing values correspond strictly to deliberate physical metrics:

- **The Document Grid**: Desktop layouts deploy a centered, reading-optimized column (maximum 720px for prose documents, 1200px for dual-pane or multi-column curation views). Surrounding chrome (sidebars, metadata palettes) aligns against a 12-column structural grid separated by 24px gutters.
- **Breakpoints**:
  - `Desktop (>= 1024px)`: Fixed left utility navigation (240px–280px), centered document stage (`#FFFFFF`), outer margins 32px.
  - `Tablet (768px - 1023px)`: Collapsible navigation drawer, 24px gutters, document sheet hugs the margins.
  - `Mobile (< 768px)`: Single-column fluid stream, 16px horizontal margins, top app bar.
- **Vertical Rhythm**: Paragraph gaps use `space-md` (16px), major subsection breaks use `space-xl` (32px), and major thematic breaks use `space-2xl` (48px).

## Elevation & Depth

This system intentionally rejects simulated lighting models, drop shadows, ambient blurs, and glassmorphic translucency. Depth is achieved strictly through:

1. **Planar Layering**: The parchment background canvas (`#F7F6F2`) sits at the lowest level. Document sheets, panels, and active modules sit atop as solid white (`#FFFFFF`) planes.
2. **1px Crisp Borders**: Separation between surfaces, toolbars, and containers is defined entirely by 1px solid borders in `#E4E2DC`.
3. **Modals & Overlays**: Floating menus and dialogs use a solid white surface with a 1px border (`#E4E2DC`), surrounded by a flat scrim of `#17181C` at 15% opacity to dim the background. No blur or shadow is applied.
4. **Structural Rules**: Visual demarcation inside containers relies on single-pixel horizontal or vertical lines rather than tinted background blocks.

## Shapes

All container perimeters, interactive buttons, inputs, and card boundaries conform to a precise corner radius:

- Standard components (buttons, input fields, cards, tooltips, dialogs) carry a uniform corner radius of **10px**.
- Nested elements (such as inner status tags or code snippets inside a card) use 6px or 8px to maintain optical concentricity.
- Full pills (`border-radius: 9999px`) are prohibited; all interactive elements retain a structured rectangular posture softened only by the 10px curve.

## Components

### Buttons
- **Primary**: Background `#1D4ED8`, text `#FFFFFF`, 10px border radius, no border. Height: 40px (desktop), padding: 0 16px. Font: Inter Medium 14px. Focus state: 2px solid `#1D4ED8` offset by 2px white space.
- **Secondary**: Background `#FFFFFF`, border 1px solid `#E4E2DC`, text `#17181C`. Hover: Background `#F7F6F2`.
- **Tertiary / Ghost**: Transparent background, text `#6B6E76`. Hover: Text `#17181C`, background `#F7F6F2`.

### Text Inputs & Form Fields
- **Container**: Solid `#FFFFFF` background, 1px solid `#E4E2DC`, 10px corner radius, height 40px, padding 0 12px. Text set in Inter 14px/16px `#17181C`.
- **Placeholder**: Set in `#6B6E76`.
- **Focus State**: Border color `#1D4ED8` with a crisp 1px outline ring in `#1D4ED8`. No soft halo.

### Cards & Document Sheets
- Solid `#FFFFFF` background encased in a 1px solid `#E4E2DC` boundary with a 10px radius.
- Padding uses `space-lg` (24px) for desktop and `space-md` (16px) for mobile. Zero drop shadow.

### Chips & Badges
- Background `#F7F6F2`, border 1px solid `#E4E2DC`, radius 6px, padding 2px 8px.
- Typographic style: Inter 12px Medium or JetBrains Mono 12px for system flags.

### Checkboxes & Radios
- 16px square (checkbox) or circle (radio), 1px solid `#E4E2DC` border, `#FFFFFF` background.
- Checked state: Fill `#1D4ED8` with a crisp white tick mark or center dot. Focus ring: 2px offset rule in `#1D4ED8`.

### Lists & Dividers
- Unordered and ordered lists use a standard 24px left indentation, 8px item gap, set in body typography.
- List items in tables or feeds are separated by a 1px continuous border in `#E4E2DC`.

### Prompt & Code Blocks
- Background `#FFFFFF` (or `#EEF2FF` for active/prompt highlights), bordered by 1px `#E4E2DC`, radius 10px, padding 16px.
- Typography: JetBrains Mono 15px with 1.6 line height.

### Callouts & Editorial Notes
- Background `#F7F6F2`, border 1px solid `#E4E2DC`, radius 10px, with an interior or anchored **2px left rule in `#1D4ED8`** indicating emphasis.