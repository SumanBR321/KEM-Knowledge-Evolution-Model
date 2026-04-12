# Design System Strategy: The Cognitive Sanctuary

## 1. Overview & Creative North Star
This design system is built to transform the chaotic process of digital information gathering into a state of "Cognitive Flow." It moves away from the aggressive, gamified aesthetics of modern SaaS and toward a high-end editorial experience.

**Creative North Star: The Cognitive Sanctuary**
The interface should feel like a private, dimly lit library for the mind—quiet, architectural, and profoundly organized. We break the "template" look by utilizing intentional asymmetry, expansive negative space, and tonal depth. Rather than a flat grid of boxes, the UI is treated as a series of floating, translucent planes that emerge from the dark, mimicking the way ideas surface from the subconscious.

---

## 2. Colors: Tonal Architecture
The palette is rooted in shadows and moonlight. We avoid harsh contrasts, preferring a "low-light" environment that reduces cognitive load and eye strain during deep work.

### The "No-Line" Rule
Standard 1px solid borders are strictly prohibited for sectioning. Structural boundaries must be defined solely through background color shifts. For example, a sidebar is defined by being `surface_container_low` against a `background` workspace. If you cannot distinguish two sections without a line, your tonal hierarchy needs adjustment.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of materials. 
- **Foundation:** `surface_container_lowest` for the deepest background layers.
- **Content Planes:** `surface_container` for primary cards.
- **Elevated Insights:** `surface_container_highest` for active nodes or focused content.
This nesting creates natural depth without visual noise.

### The "Glass & Gradient" Rule
To achieve a premium feel, floating elements (modals, popovers, hovering tooltips) should utilize a "Frosted Indigo" glass effect: 
- **Fill:** `surface_variant` at 60% opacity.
- **Backdrop Blur:** 12px to 20px.
- **Signature Texture:** Use a subtle linear gradient on primary CTAs (`primary` to `primary_container`) at a 135-degree angle to provide a "soul" to the action, avoiding the flat, plastic look of standard buttons.

---

## 3. Typography: The Editorial Voice
We use a dual-font system to balance intellectual authority with technical precision.

*   **Display & Headlines (Manrope):** Chosen for its geometric but warm character. Used in `display-lg` through `headline-sm` to create an "Editorial Masthead" feel. Headlines should use tight letter-spacing (-0.02em) to feel cohesive.
*   **Body & UI (Inter):** The workhorse. Used for `title-md` down to `label-sm`. Inter’s high x-height ensures readability in the dense information environments of a knowledge system.

**Hierarchy as Narrative:**
Use extreme scale contrast. A large `display-sm` headline next to a `body-sm` metadata label creates a sophisticated, magazine-style layout that signals "organized intelligence."

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are too "web 2.0" for this system. We use light and tone to imply height.

*   **The Layering Principle:** Depth is achieved by "stacking." Place a `surface_container_high` card on top of a `surface_container_low` background to create a soft, natural lift.
*   **Ambient Shadows:** For floating elements like Chrome extension popups, shadows must be extra-diffused. 
    *   *Shadow Rule:* `blur: 40px`, `spread: -5px`, `color: rgba(0, 0, 0, 0.4)`. 
    *   The shadow should be tinted with the `on_surface` color at 4% opacity to mimic natural light absorption.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, it must be a "Ghost Border": use the `outline_variant` token at 15% opacity. Never use 100% opaque borders.

---

## 5. Components: Precision Primitives

### Buttons
- **Primary:** Gradient-filled (`primary` to `primary_container`), `xl` roundedness. No border. Text is `on_primary_fixed`.
- **Secondary:** Ghost style. No background. `outline_variant` ghost border (15% opacity).
- **Tertiary:** Purely typographic. Use `primary_fixed` color with a 2px underline appearing only on hover.

### Chips (The Knowledge Atoms)
Chips represent individual concepts. They should be `surface_container_highest` with `label-md` text. Use `secondary` for the icon to denote "connections" between ideas.

### Input Fields
- **Background:** `surface_container_low`.
- **Border:** None in resting state.
- **Active State:** A subtle 1px "Ghost Border" using `primary` at 30% opacity and a soft inner glow.
- **Typography:** Placeholder text must be `on_surface_variant`.

### Cards & Lists: The "Air" Rule
- **Forbid Dividers:** Do not use lines to separate list items. 
- **Spatial Separation:** Use 12px to 16px of vertical white space (from the Spacing Scale) to create groups.
- **The "Aha" Insight:** Any AI-generated insight uses a `tertiary_container` background with a `tertiary` (Warm Amber) left-side accent "shimmer" (a 2px wide vertical glow) to signal a breakthrough moment.

### Additional Component: The Evolution Node
A specialized component for KEM. A circular container (`full` roundedness) using `surface_bright` with a `secondary` glow effect, used to represent "Parent" or "Root" concepts in the knowledge graph.

---

## 6. Do's and Don'ts

### Do
- **Do** embrace asymmetry. Center-aligning everything feels like a template; left-aligning with generous right-side margins feels like a professional tool.
- **Do** use `tertiary` (Warm Amber) sparingly. It is a "reward" color, reserved only for meaningful insights.
- **Do** prioritize "Breathing Room." If a screen feels cluttered, increase the padding to the `xl` or `2xl` scale before removing content.

### Don't
- **Don't** use pure black (#000000). Always use `surface_container_lowest` to maintain the "blue-near-black" sophisticated depth.
- **Don't** use standard "Success" greens for AI confirmations. Use the `soft teal` (#2DD4BF) to maintain the calm, cool temperature of the system.
- **Don't** use motion that is "bouncy" or "snappy." All transitions should be slow, linear-out-slow-in (300ms+), mimicking the steady pace of human thought.