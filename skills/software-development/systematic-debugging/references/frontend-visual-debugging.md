# Frontend Visual Debugging: CSS Positioning & Alignment

## The 4-Phase Process Still Applies

CSS positioning bugs look different from code bugs, but the methodology is the same:
**Gather evidence → find root cause → hypothesis → fix.**

## Common CSS Positioning Pitfalls

### 1. `inline-block` Baseline Extra Height

**Symptom:** A percentage-positioned child (e.g. `absolute left-1/2 top-1/2`) doesn't center relative to a sibling.
**You tweak `top: 35%` and it "looks right" but feels wrong.**

**Root cause:** `inline-block` containers with `inline-block` children reserve space for text descenders/baseline alignment. The parent renders *taller* than the child, so `top: 50%` is calculated against the inflated parent height, not the sibling's actual center.

**Detection (browser console):**
```js
// Compare parent vs child rendered dimensions
JSON.stringify({
  parentW: parent.offsetWidth,
  parentH: parent.offsetHeight,
  childW: child.offsetWidth,
  childH: child.offsetHeight
})
```

**Fix:** Replace `relative inline-block` with explicit sizing + flex centering:

```tsx
// ❌ Off-center due to baseline padding
<div className="relative inline-block">
  <div className="absolute left-1/2 top-1/2 ..."> {/* orbits */} </div>
  <div className="inline-block"> {/* avatar */} </div>
</div>

// ✅ Precise center: explicit size + flex
<div className="relative size-24 flex items-center justify-center">
  <div className="absolute left-1/2 top-1/2 ..."> {/* orbits */} </div>
  <Avatar className="size-24 ..." />
</div>
```

**Key insight:** The container must match the child's expected dimensions exactly. `size-24` (96px) gives a single source of truth that both the flex layout and percentage positioning reference.

### 2. CSS Animation Transform-Origin Offset (OrbitingCircles & Similar)

**Symptom:** After fixing `inline-block` baseline (pitfall #1), orbit/animated elements still appear offset to the bottom-right. Perfect pixel math says `left: 50%; top: 50%` should center, but visual shows ~16px offset.

**Root cause:** CSS animation libraries (magicui's `OrbitingCircles`, framer-motion's orbit patterns, any `rotate() translateY() rotate()` animation) use `transform-origin: 50% 50%` (the CSS default). The orbit rotates around the icon's own center, not its top-left corner.

When the icon is `position: absolute; left: 0; top: 0` inside a `w-0 h-0` anchor at the avatar center:

- Icon top-left → avatar center (632.5, 128)
- Icon center (transform-origin) → (632.5 + iconSize/2, 128 + iconSize/2)
- For 32px icons: orbit center = (avatarCenter + 16px, avatarCenter + 16px)
- **Effective orbit center is 16px right + 16px below avatar center**

**Detection (browser console):**
```js
// Measure icon transform-origin vs avatar center
const icon = document.querySelector('[class*="animate-orbit"]');
const avatar = document.querySelector('[data-slot="avatar"]');
const aRect = avatar.getBoundingClientRect();
const iRect = icon.getBoundingClientRect();

const avatarCenter = { x: aRect.left + aRect.width/2, y: aRect.top + aRect.height/2 };
const iconCenter = { x: iRect.left + iRect.width/2, y: iRect.top + iRect.height/2 };

console.log('transform-origin:', getComputedStyle(icon).transformOrigin);
console.log('Avatar center:', avatarCenter);
console.log('Icon center (effective orbit pivot):', iconCenter);
console.log('Offset:', {
  x: iconCenter.x - avatarCenter.x,
  y: iconCenter.y - avatarCenter.y
});
```

Also verify the w0h0 anchor position:
```js
const w0h0 = /* container that has left:0;top:0 orbit children */;
console.log('w0h0 rect:', w0h0.getBoundingClientRect());
console.log('Effective orbit center:', {
  x: w0h0.getBoundingClientRect().left + 16,  // + iconSize/2
  y: w0h0.getBoundingClientRect().top + 16    // + iconSize/2
});
```

**Fix: Offset the orbit anchor by `-(iconSize/2)`**

Replace `left: 50%; top: 50%; translate(-50%, -50%)` with `calc()` to pre-compensate for the transform-origin offset:

```tsx
// ❌ Orbit center at (avatarCenter + 16px, avatarCenter + 16px)
<div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
  <div className="relative w-0 h-0">
    <OrbitingCircles iconSize={32}>...</OrbitingCircles>
  </div>
</div>

// ✅ Orbit center exactly at avatar center
<div className="absolute pointer-events-none"
     style={{ left: 'calc(50% - 16px)', top: 'calc(50% - 16px)' }}>
  <div className="relative w-0 h-0">
    <OrbitingCircles iconSize={32}>...</OrbitingCircles>
  </div>
</div>
```

The `16px` is `iconSize / 2` (32 / 2 = 16). If `iconSize` changes, adjust the calc offset accordingly.

**Key insight:** The `-translate-x-1/2 -translate-y-1/2` approach doesn't work here because the wrapper div has 0×0 dimensions (due to `w-0 h-0` child), so `-50%` of 0 = 0 — no effective translation.

### 3. Ring/Border on Absolute Child

**Symptom:** A `ring` or `outline` on a positioned element causes the parent to measure larger than expected.

**Root cause:** Rings (`box-shadow` with offset) don't affect layout, but `outline` does. Verify which visual effect is in use.

**Detection:** Compare `getComputedStyle(el).boxShadow` vs `getComputedStyle(el).outline`.

### 4. `transform` and `position: fixed` Reference Frame

**Symptom:** A `fixed` child is positioned relative to the viewport... except when an ancestor has `transform`, `filter`, or `perspective` — then it's relative to that ancestor.

**Root cause:** Any ancestor with `transform: translate(...)`, `filter: blur(...)`, or `perspective` creates a new containing block for `fixed` children.

**Detection:** Walk up the DOM tree checking for `transform` / `filter` / `perspective`:
```js
let el = element;
while (el) {
  const style = getComputedStyle(el);
  if (style.transform !== 'none' || style.filter !== 'none') {
    console.log('⚠️ New containing block ancestor:', el);
  }
  el = el.parentElement;
}
```

### 5. Percentage Padding/Margin in Flex Context

**Symptom:** Percentage padding doesn't behave as expected inside a flex container.

**Root cause:** In flex layout, percentage padding on a flex child is calculated relative to the *parent's inline size* (width), not the child's own width. Top/bottom padding percentages also use width in horizontal writing modes.

## Browser Console Measurement Techniques

Always measure rather than guess:

```js
// Get rendered dimensions of key elements
function measure(el, label) {
  const rect = el.getBoundingClientRect();
  const style = getComputedStyle(el);
  return {
    label,
    offsetW: el.offsetWidth,
    offsetH: el.offsetHeight,
    rectW: rect.width,
    rectH: rect.height,
    left: style.left,
    top: style.top,
    transform: style.transform,
    display: style.display,
  };
}

// Compare orbit center vs avatar center
const container = document.querySelector('.relative.flex');
const avatar = container.querySelector('[data-slot="avatar"]');
const orbitAnchor = container.querySelector('.absolute');
console.log('Container:', container.getBoundingClientRect());
console.log('Avatar center:', {
  x: avatar.getBoundingClientRect().left + avatar.offsetWidth / 2,
  y: avatar.getBoundingClientRect().top + avatar.offsetHeight / 2
});
console.log('Orbit anchor:', orbitAnchor.getBoundingClientRect());
```

## When to Suspect a Containing Block Issue

The user says "X% looks like center but 50% doesn't." This always means the parent container's rendered size doesn't match expectations. Measure first, hypothesize second.

## Two-Stage Debugging Pattern: Compound Pitfalls

The inline-block (pitfall #1) and transform-origin (pitfall #2) bugs **frequently compound** — you fix one, test, and the other remains. Don't treat this as a failed fix; it's expected.

**Session trace:**
1. User says "center looks bottom-right" → measure container: 96×103 (7px extra from inline-block baseline)
2. Fix: `relative inline-block` → `relative size-24 flex items-center justify-center` → container now 96×96
3. User still says "looks bottom-right" → new measurement: orbit anchor at avatar center, BUT transform-origin shifts effective center by +16px each axis
4. Fix: `left: 50%; top: 50%; translate(-50%, -50%)` → `style={{ left: 'calc(50% - 16px)', top: 'calc(50% - 16px)' }}`

**Lesson:** After any CSS position fix, re-measure BEFORE declaring done. The second bug was invisible until the first was resolved.

## Debugging Checklist for Orbiting/Animation Centering

When an animated element's rotation center doesn't align with the visual center:

1. [ ] Fix inline-block first: measure parent vs child dimensions → `getBoundingClientRect()`
2. [ ] Then re-measure orbit center: is it still off? → Check transform-origin next
3. [ ] What is the child icon's `transform-origin`? → `getComputedStyle(icon).transformOrigin`
4. [ ] Is the child at `left: 0; top: 0`? → Effective orbit center = parentOrigin + (iconSize/2)
5. [ ] Does `-translate-x-1/2` have any effect? → Only if the element has non-zero dimensions
6. [ ] Verify with pixel math: avatarCenter vs effectiveOrbitCenter
7. [ ] After fix, verify dev server hot-reloaded: check `getComputedStyle(el).left` matches expected Tailwind class
