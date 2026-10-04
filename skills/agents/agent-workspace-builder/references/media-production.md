# Produce editable media

## Contents

- Creative contract
- Images and design
- Video from idea to delivery
- Audio and understanding
- Timeline changes
- Acceptance

## Creative contract

Capture audience, purpose, core claim, brand references, exact required text, output formats, length, aspect ratios, publication destination, rights/consent, budget, and reference assets. Reuse explicit user choices. Make informed reversible choices when details are absent. Do not invent customer testimonials, product performance, or personal experiences for UGC-style material.

Choose **draft** for fast concept validation, **standard** for a complete polished deliverable, or **premium** for additional alternatives and review within budget. These are workflow profiles, not provider model names. Never assume an advertised model produces every requested format.

## Images and design

1. Inspect source images and brand assets. Record what must remain unchanged.
2. Select actual image generation for photographic/illustrative assets; use vector/code tools for exact charts, diagrams, UI text, and existing SVG edits.
3. Write the prompt around subject, composition, style, lighting, references, exact text, and invariants. Use native-tool or provider-supported reference/mask controls.
4. Produce a draft, inspect it visually, and repair specific defects. Preserve character/product identity, alpha, proportions, and crop requirements.
5. Put important copy in editable text layers when feasible; verify spelling, names, numbers, and logos. Do not pretend raster text is editable typography.
6. Deliver original-resolution assets, requested crops, previews, alt text, and source/provenance metadata. Check actual dimensions and transparency.

For design-view parity, implement region selection, mask/reference assets, before/after preview, non-destructive versions, undo, and text layers. A natural-language edit that preserves the original by luck does not prove region-edit controls.

## Video from idea to delivery

1. Research factual claims and references when needed. Store citations for on-screen facts and licenses for found material.
2. Write a timed script and shot list. Allocate narrative beats and duration; choose what needs generation, user footage, stock, or code-made motion graphics.
3. Create a storyboard and a short style bible: characters, products, palette, lighting, camera language, typography, pacing, sound, and exclusions.
4. Produce reusable references/keyframes. Use image-to-video or other supported controls when consistency matters. Check exact support for first/last frame, multiple references, camera control, native audio, extension, and lip sync.
5. Submit independent shots within concurrency and budget caps. Persist each attempt; keep good shots when repairing another. Track provider IDs and unresolved charges.
6. Ingest user clips: probe metadata, make proxies, sample frames, transcribe audio, and select usable segments. Preserve originals and timecode mappings.
7. Assemble a versioned timeline using `assets/timeline.example.json` as a contract example. Keep clips, image plates, captions, editable text, motion graphics, narration, music, and effects separate.
8. Render previews at low cost. Inspect opening, transitions, text-heavy frames, continuity, product identity, lip sync, pacing, audio mix, and ending. Verify factual overlays against source data.
9. Render the requested final formats and aspect ratios. Reframe intentionally rather than blindly crop faces or text. Save MP4 or requested delivery format, caption files, poster frame, editable project, source assets, and a manifest.

Use deterministic rendering (for example, an existing Remotion or FFmpeg pipeline) for timed typography, charts, UI demonstrations, and layout. Confirm installed tools and render budgets. Generated imagery must not substitute for exact data graphics. Keep motion graphics source code so values and timing can change without regenerating footage.

Use current provider models chosen from verified schemas; do not bake a supposedly “best” model into the skill. For realistic UGC, write as a demonstration or clearly fictional spokesperson when there is no real user testimony. Never clone a person's voice or imply their endorsement without appropriate permission.

## Audio and understanding

For narration, verify speaker identity/consent, language, pronunciation, speaking pace, and output format. Create a pronunciation list for brands and technical terms. Preserve separately editable narration/music/effects stems and caption alignment.

For music and effects, record the source and usage rights. Avoid claiming commercial rights without the provider's terms for the actual account and asset. Mix speech intelligibly; inspect for clipping, abrupt cuts, and silence gaps.

For transcription, save timestamps and speaker labels; mark uncertain words/names instead of inventing them. For long recordings, chunk with overlap and reconcile boundaries. Distinguish spoken evidence from inferred action items; a meeting request is not authorization to message attendees.

For video understanding, combine audio transcript and sampled frames with timestamps. Report sampling limits. Do not claim to have inspected every frame unless the actual method supports it.

## Timeline changes

Give every asset and timeline element a stable ID. Store source in/out points, destination times, track type, transform, effects, volume, text, and provenance. Human edits increment a revision. Agent edits require that expected revision and affect only specified elements.

A request such as “lower the music and shorten shot three” should change two timeline properties while retaining the other accepted assets. Re-render dependent segments and final export, not all generations. Keep dependency hashes so changes invalidate the correct renders. Ensure caption timings follow trims and speed changes.

Provide a real timeline UI for full editor parity: playhead, preview, selection, trim/split/move, track visibility/mute, text/caption editing, volume/keyframes, undo/redo, asset replacement, autosave/conflict handling, and export progress/cancel. If only a source JSON/renderer exists, label visual editing as unimplemented.

## Acceptance

Probe files for codec/container, duration, frame rate, dimensions, audio channels, and decodability. Inspect visual output and listen to audio with available tools; metadata checks cannot replace perceptual review. Verify captions and safe areas on the target layout. Offer reduced-motion variants when relevant and avoid hazardous flashing.

Deliver an editable source project that can reproduce the final export, with relative asset references or a self-contained bundle. Verify a small real edit and re-render. A flattened video plus a prose storyboard does not meet the editable-source requirement.
