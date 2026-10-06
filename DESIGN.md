---
name: Synapse Sentinel
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#849495'
  outline-variant: '#3b494b'
  surface-tint: '#00dbe9'
  primary: '#dbfcff'
  on-primary: '#00363a'
  primary-container: '#00f0ff'
  on-primary-container: '#006970'
  inverse-primary: '#006970'
  secondary: '#deb7ff'
  on-secondary: '#4a007f'
  secondary-container: '#6b13af'
  on-secondary-container: '#d4a5ff'
  tertiary: '#d8ffe7'
  on-tertiary: '#003824'
  tertiary-container: '#65f2b5'
  on-tertiary-container: '#006d4a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#7df4ff'
  primary-fixed-dim: '#00dbe9'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#f1dbff'
  secondary-fixed-dim: '#deb7ff'
  on-secondary-fixed: '#2d0050'
  on-secondary-fixed-variant: '#680eac'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  mono-metric-lg:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.02em
  mono-metric-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0em
  mono-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-dense: 0.375rem
  margin: 1rem
  margin-compact: 0.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes an ultra-high-reliability, mission-critical operational interface for Enterprise AI Edge & Biometric Surveillance. The target users are edge compute engineers, enterprise security operations center (SOC) directors, biometric forensic analysts, and infrastructure automated response supervisors. 

The emotional response must convey absolute precision, sub-millisecond responsiveness, authoritative computational depth, and hyper-vigilance without causing operator fatigue during prolonged continuous shifts. 

The aesthetic is **Tactical Cybernetic Precision**—a calibrated synthesis of high-density technical minimalism, structural utilitarian brutalism, and controlled luminescent telemetry. Interfaces prioritize data throughput, optical clarity, deterministic spatial hierarchy, and zero ambiguous ornamentation. Every decorative artifact must derive purely from state monitoring, bounding vectors, signal latency, and neural confidence distributions.

## Colors

The palette operates under a default dark mode architecture designed for low-lux security operations centers, anchored by deep obsidian and cold slate foundations. Contrast ratios consistently satisfy WCAG 2.1 AAA for terminal streams and AA for ambient operational layers.

### Palette Architecture
- **Obsidian / Slate Neutral Tiers**:
  - `canvas-base`: `#070A11` (Deep void black; absolute canvas floor)
  - `surface-node`: `#0F172A` (Primary structural panel, card baseline)
  - `surface-elevated`: `#1E293B` (Interference trays, flyouts, and modal panels)
  - `surface-highlight`: `#334155` (Hover states, splitters, perimeter node delimiters)
  - `text-muted`: `#64748B` (Inactive metadata, system timestamps)
  - `text-regular`: `#94A3B8` (Descriptive labels, secondary parameters)
  - `text-bright`: `#F8FAFC` (Critical identification labels, primary readouts)

- **Chromatics & Telemetry Signifiers**:
  - **Primary (`#00F0FF` - Cyber Cyan)**: Optical targeting vectors, active facial bounding matrices, focused edge node pings, primary interactives, and real-time telemetry spikes.
  - **Secondary (`#7B2CBF` - Electric Violet)**: Deep neural model classification, regional edge aggregation gateways, latent inferencing, and semantic segmentation tags.
  - **Tertiary / Nominal (`#10B981` - Emerald Signal)**: Hardware nominal, inference verified, sync validated, FPS target matched, biometric confidence ≥ 92%.
  - **Alert Amber (`#F59E0B`)**: Inference divergence, degraded node bandwidth, thermal throttling threshold reached, confidence drift (60%–91%).
  - **Critical Crimson (`#EF4444`)**: Identity blacklist match, zero-frame drops, node offline, edge tamper trip.

Surfaces use alpha-layered chromatic accents (`rgba(0, 240, 255, 0.08)` to `rgba(0, 240, 255, 0.25)`) to map dynamic neural detection fields directly onto visual data without obscuring raw optical inputs.

## Typography

The typography implements a dual-structure operational model:
1. **Geometric Human-Machine Interface**: **Space Grotesk** serves for structural headings, device manifests, and analytical summaries. **Inter** handles narrative audit logs, identity profiles, incident descriptions, and settings.
2. **Computational Tabular Monospace**: **JetBrains Mono** is enforced strictly across all runtime data feeds, inference scores, confidence intervals, UTC timestamps, edge node IP/MAC allocations, latency measurements, and CSV column reconciliations.

### Typographic Rules
- Never use non-monospace fonts for fluctuating dynamic numbers. Monospace numbers maintain spatial stability, avoiding layout twitching during high-frequency screen updates (60fps to 120fps streaming readouts).
- All operational badges and status tags must leverage `label-caps` in uppercase with explicit tracking (`letterSpacing: 0.08em`) to guarantee quick recognition under high-stress visual sweeps.
- Monospace decimal data should consistently align to the right within data grids, while contextual parameters align left.

## Layout & Spacing

This design system uses a micro-density layout structure engineered for complex, multi-viewport surveillance grids and multi-monitor telemetry setups.

### Density Philosophy
- Standard enterprise whitespace is compressed by 40% using the `0.25rem` (4px) baseline index to maximize pixel utility while preventing overlapping optical stress.
- Primary visual layouts rely on a **12-column or 24-column nested CSS Subgrid** with dynamic column tracking. Gaps scale strictly based on context (`gutter-dense` for camera/feed matrices and `gutter` for platform analytics and incident tables).

### Form Factors & Breakpoints
- **Ultra-Wide Surveillance Walls (≥1920px up to 3840px)**: 24-column layout. Camera feeds arrange in deterministic 4×4 or 6×6 dense arrays with persistent sidebars for telemetry and triage feeds. Margins fixed at `1rem`.
- **Desktop/Workstation (1280px - 1919px)**: 12-column layout. Camera matrix auto-scales to 2×2 or 3×3 with toggleable side-drawers for CSV reconciliation and edge orchestration.
- **Ruggedized Field Tablet (768px - 1279px)**: 8-column layout. Feed grids prioritize high-priority detections, switching telemetry streams into swipeable off-canvas sheets. Margins drop to `margin-compact` (`0.5rem`).
- **Tactical Handheld Mobile (<768px)**: 4-column layout. Single-feed presentation with bottom-sheet triage and vertical timeline-based audit feeds.

## Elevation & Depth

Visual hierarchy does not use diffuse, cloudy drop shadows, which reduce readability on high-density black terminals. Depth is achieved entirely through **Tonal Surface Layering**, **Crisp Structural Borders**, and **Targeted Photonic Glows**.

### Tiers of Elevation
- **Level 0 (Canvas Base `#070A11`)**: Deep structural background for stream canvases, unrendered canvas regions, and global workspace framing.
- **Level 1 (Node Surface `#0F172A`)**: Base container for feed monitors, analytical panels, and hardware diagnostic tables. Defined by a 1px border of `rgba(51, 65, 85, 0.6)`.
- **Level 2 (Active Structural `#1E293B`)**: Interactive cards, selected node rows, focused search bars, and floating operational bars. Outlines switch to `rgba(0, 240, 255, 0.4)` on selection.
- **Level 3 (Modal Surface & Reconciliation Drawers `#1E293B`)**: Overlaid system states, forensic inspection drawers, and CSV validation monitors. Border is 1px solid `#334155` complemented by a sharp outer inset highlight: `box-shadow: 0 0 0 1px rgba(0, 240, 255, 0.2), 0 8px 24px rgba(0, 0, 0, 0.8)`.

### Photonic Telemetry Accents
- Normal elements use zero blur.
- High-priority operational nodes (e.g., identity match, edge disconnect) project a restrained 4px to 8px saturated glow:
  - Cyber Cyan targeting: `0 0 8px rgba(0, 240, 255, 0.45)`
  - Critical Alert: `0 0 12px rgba(239, 68, 68, 0.5)`

## Shapes

The geometric framework follows an architectural, hard-engineered approach. Standard radius tokens operate at `0.25rem` (Level 1 - Soft), maintaining crisp, chiseled edges that align with engineering and analytical instruments.

### Geometry Token Specs
- **Default Geometry (`rounded-sm`)**: 2px to 4px (`0.25rem`). Applied to telemetry metrics, cards, inputs, camera viewport frames, and modal structures.
- **Pill Exceptions (`rounded-full`)**: Prohibited for standard interactive buttons. Restricted strictly to high-level system vitality tags (e.g., "LIVE", "EDGE READY") and identity status indicator pips.
- **Clipping & Chamfer Details**: Biometric targeting vectors and edge node cards feature simulated 45-degree micro-chamfers or corner-bracket graphic overlays (`2px × 2px` corner accents), referencing target reticles and optical sensor viewfinders.

## Components

### 1. Buttons & Controls
- **Primary Cybernetic Button**: Background `rgba(0, 240, 255, 0.1)`, 1px border solid `#00F0FF`, text `#00F0FF`. On hover: background `#00F0FF`, text `#070A11`, box-shadow `0 0 10px rgba(0, 240, 255, 0.4)`. Font: `Space Grotesk`, medium, 12px, tracking `0.04em`.
- **Secondary Ghost Button**: Background `transparent`, 1px border solid `#334155`, text `#94A3B8`. On hover: border-color `#64748B`, text `#F8FAFC`.
- **Destructive/Override Button**: Background `rgba(239, 68, 68, 0.12)`, 1px border solid `#EF4444`, text `#EF4444`. On hover: background `#EF4444`, text `#FFFFFF`.

### 2. High-Density Biometric Feed Cards
- Structure: Wrapped in `#0F172A` with a 1px border of `#1E293B`. Top bar displays Edge Node ID (`JetBrains Mono`, 11px) left-aligned, alongside real-time FPS counter and network round-trip time (`RTT: 4.2ms`).
- Video Surface: Integrated HUD overlays. Detected entities receive an SVG vector bounding box (1px solid cyan for recognized, 1px amber/crimson dashed for unknown or watchlisted).
- Reticle Bounding Anchors: 4px corner tick-marks extending beyond the main box.
- Confidence Badge Anchor: Bound to the upper-right corner of the detection box. Format: `JetBrains Mono`, 10px, background `rgba(7, 10, 17, 0.85)`, color `#00F0FF`, 1px solid `#00F0FF`. Displays model name and score: `FACENET-V4 // 98.4%`.

### 3. Multi-Tier Node Status Indicators
- **Tier 1 (Local Edge)**: Compact pill container with an emerald pulsing LED dot (`#10B981`), labeled `EDGE-L1`. Metric displays hardware core temperature and on-device VRAM usage.
- **Tier 2 (Regional Gateway)**: Electric violet indicator (`#7B2CBF`), labeled `GATEWAY-R2`. Metric displays buffer depth and message throughput.
- **Tier 3 (Central Cloud)**: Cyber cyan indicator (`#00F0FF`), labeled `CLOUD-C3`. Metric displays synchronization delta and API ping.
- Disconnected or degraded states override indicator colors to `#F59E0B` (degraded) or `#EF4444` (unreachable), swapping the continuous pulse animation to a rapid strobe.

### 4. Manual CSV Sync Reconciliation Drawer & Tables
- Slide-out tray anchored to the right workspace boundary (`#0F172A`, 480px width), with 1px border-left `#334155`.
- Data Tables: Fixed headers, alternating row striping via `#070A11` and `#0F172A`. Cells sized at dense 28px height.
- Reconciliation Elements: Split-row data display displaying `LOCAL BIOMETRIC HASH` vs `INGESTED CSV ENTITY`. Discrepancies highlight automatically in bold amber (`#F59E0B`) with inline action buttons to "FORCE EDGE OVERRIDE" or "DISCARD CSV RECORD".

### 5. Live Audit Telemetry Grids
- Real-time terminal output styled with `JetBrains Mono` at 11px font size.
- Left-hand column: ISO-8601 UTC microsecond timestamps in `#64748B`.
- Middle column: Event taxonomy identifier (e.g., `[INFERENCE_OK]`, `[MATCH_ALERT]`, `[SYNC_FAIL]`) wrapped in bracketed color tags.
- Right-hand column: Event details with automatic highlighting for extracted variables (MAC addresses, subject UUIDs, confidence floats).

### 6. Inputs, Checkboxes & Switches
- **Input Fields**: Background `#070A11`, 1px border `#334155`, font `JetBrains Mono` 12px, text `#F8FAFC`. Focus state: border `#00F0FF`, zero outline, with an ambient cyan inner glow (`box-shadow: inset 0 0 4px rgba(0, 240, 255, 0.2)`).
- **Checkboxes**: Hard-edged square (0px to 2px radius), 14px × 14px, border 1px solid `#334155`, background `#070A11`. Checked state: background `#00F0FF`, border `#00F0FF`, with an obsidian checkmark graphic.
- **Node Toggle Switch**: Rectangular 28px × 14px track, 1px border `#334155`, `#070A11` background. Thumb is a 10px × 10px flat block moving horizontally, illuminated in `#00F0FF` when active.