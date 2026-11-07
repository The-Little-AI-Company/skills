# First-screen rubric

Read this in step 7. Apply it to the rendered page beside the three exemplars, never to the Markdown source. A human or a judge model can score from a screenshot of each theme.

The first screen is what fits above the fold at the render width: 1012px wide and about 800px tall. Depth below the fold is the one category that reads further. All anchors and scales here are opinion, and no study validates them.

## How to score

- Score each category from 1 to 10. The anchors define 5, 7 and 9. Use the numbers between when a page sits between anchors.
- A 5 is competent and forgettable. A 7 matches a good repository of the type. A 9 matches the best exemplar you opened.
- Score the worse theme. A page that breaks in dark mode does not score its light-mode value.
- Give one sentence of evidence per category, naming what is on the page.
- Report all eight scores. Do not average them into a pass. The page is done when each category meets or beats the three exemplars, as SKILL.md says.
- A broken image, a dead badge or a false claim caps Polish and Credibility at 3, whatever else is true.

## Pitch and proof are separate

Pitch and proof are two jobs, and this rubric scores them apart.

- **Pitch** earns attention and lives on the first screen. Clarity, Visual impact, Next step and Hierarchy score the pitch.
- **Proof** earns trust and lives lower down. Credibility and Depth score the proof.
- Do not raise a pitch score for receipts on the first screen. A dated caption, a test log or a list of what was verified there lowers Hierarchy.
- Do not excuse a false pitch because the proof section is honest. Every claim on the first screen must be true, whether or not it carries its receipt there.

## 1. Clarity of purpose in 5 seconds

Can a stranger say what this is and who it is for after 5 seconds?

- **5.** The category is clear, such as "a logging library". What makes it useful takes reading further, or the sentence relies on project jargon.
- **7.** One sentence says what it does for the reader, in plain words. A stranger could repeat it. It competes with one or two other things for attention.
- **9.** The sentence and the visual together answer what it is, who it is for and why it beats the obvious alternative, with nothing else needed. Example: the one-line tagline and immediate code sample of psf/requests.

## 2. Visual impact

Does the page show the thing, at a quality the project deserves?

- **5.** Plain text or a generic logo for a project that has something to show. Nothing is wrong, and nothing is memorable.
- **7.** One real image or demo from the running product, in focus, cropped and readable at column width. For a code-first project, a syntax-highlighted sample that does the same job.
- **9.** The visual makes the point by itself: a reader understands the product from it without the caption. It uses realistic data and works in both themes. Example: the per-command demos of charmbracelet/gum.

A project with no visual surface, such as an SDK, scores on its code sample. An image added only to raise this score lowers Fit.

## 3. Credibility

Would a skeptical reader trust the page after checking?

- **5.** No false claims, but numbers and superlatives have no source, and the reader has to take them on faith.
- **7.** Each number has a date, method or link. Badges are live and report something tested. Limits are stated somewhere findable.
- **9.** Claims hold up under checking, with the method shown so a reader could repeat it. The page says who should not use this. Examples: the benchmark method in BurntSushi/ripgrep and the "when shouldn't I use it" section in huggingface/transformers.

## 4. Next step

Does the reader know what to do after reading?

- **5.** Install steps exist, but the reader must scroll or hunt. Several actions compete.
- **7.** One clear action sits within the first screen or just below it, such as a command, a download or a docs link.
- **9.** The action fits the audience from step 1, can be copied as is, and works on a clean checkout. Secondary actions are visibly secondary.

## 5. Hierarchy

Does the eye land in the right order?

- **5.** All the parts are present, but sponsors, notices, badges or a contents list arrive before the purpose, or they compete with it.
- **7.** The order runs name, purpose, visual, action. Badges sit quietly. Little else appears above the fold.
- **9.** Every element on the first screen earns its place, and removing any one would hurt. Examples: the shell of vercel/next.js and the link bar of plausible/analytics.

## 6. Polish

Does the page look cared for?

- **5.** It renders correctly in the main theme. Image widths are inconsistent, or one element looks unconsidered.
- **7.** Both themes work, images are sharp and sized consistently, and alt text is present. No dead images or link rot appears on the first screen.
- **9.** Theme handling is deliberate through `<picture>`, badge styles match, spacing is even, and images load fast. Nothing looks accidental at any point on the page.

## 7. Depth below the fold

Does the rest of the page keep the first screen's promise?

- **5.** Sections exist, but they read as a template, or the page stops at install.
- **7.** Sections answer the reader's next questions in order, and the page links out for reference and policy. Commands and numbers are right.
- **9.** A reader can go from first look to working use without leaving, or the page routes them precisely. Proof, limits, status and support are easy to find. Examples: the task recipes of actions/checkout and the routing of vercel/next.js.

## 8. Fit to type

Does this look like the best of its kind, or like a different kind of project?

- **5.** The page follows a generic template, such as a framework with an app-style hero or an SDK with no requirements section.
- **7.** The page follows its chosen preset and the type's norms from [presets.md](presets.md), and its length suits the audience.
- **9.** It reads as an example others in the type would copy. It takes the type's strongest move and adds one of its own, and every departure from the norm has a reason.

## Scorecard

| Category | Job | This page | Exemplar 1 | Exemplar 2 | Exemplar 3 | Evidence |
|---|---|---|---|---|---|---|
| Clarity | Pitch | | | | | |
| Visual impact | Pitch | | | | | |
| Next step | Pitch | | | | | |
| Hierarchy | Pitch | | | | | |
| Credibility | Proof | | | | | |
| Depth below the fold | Proof | | | | | |
| Polish | Both | | | | | |
| Fit to type | Both | | | | | |

Fix the lowest category first, render again and rescore.
