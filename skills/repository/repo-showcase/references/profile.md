# Profile README

Read this in step 5 when the repository is a GitHub profile. A profile answers who this person or organization is and where to look next. The owner's taste decides the style. The owner approves all text published in their name.

Facts were read on 2026-11-06. The audience section and all style advice here are opinion, with no study behind them.

## GitHub requirements

**Personal profile.** [GitHub's rules](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme): a public repository named exactly as the username, with a non-empty `README.md` at the root.

**Organization profile.** [GitHub's rules](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/customizing-your-organizations-profile): a public repository named `.github` holding `profile/README.md`. A member-only version goes in a private repository named `.github-private`, at the same path.

`exemplars.py` cannot search this type. Use the four exemplars below, and open any other profiles you admire by hand.

## Options

Offer two or three. Go up this list only when the owner has something to feed it.

| Option | Holds | Upkeep | Exemplar |
|---|---|---|---|
| Plain | A few lines and a link | None | [kentcdodds/kentcdodds](https://github.com/kentcdodds/kentcdodds): 9 lines, one image with descriptive alt text, one link |
| Curated | Name, what you work on, 3 to 5 links to work | Edit when work changes | None measured |
| Visual | Local images or a banner | Low. Keep alt text | [sindresorhus/sindresorhus](https://github.com/sindresorhus/sindresorhus): 14 relative GIFs, all local, but 14 lack alt text |
| Live | Marked blocks rewritten by a scheduled workflow, such as recent releases and posts | A workflow to keep healthy | [simonw/simonw](https://github.com/simonw/simonw): live content, no stat cards, 61 lines |
| Cards | Stat cards from a hosted or self-hosted service | A service dependency | See below |
| Maximal | Banners, cards, sponsor lists and label badges | High | [DenverCoder1/DenverCoder1](https://github.com/DenverCoder1/DenverCoder1): 38 images plus 82 label badges, and it runs its own stats instance |

Header badges were 0 in three of these four exemplars, and the fourth has 1.

## Live content

Live content works well because it shows current work without a claim. The pattern:

1. Mark regions in the README with HTML comments.
2. A scheduled GitHub Actions workflow fetches recent releases, posts or similar, and rewrites those regions.
3. The workflow commits only if content changed.

Give the workflow the narrowest token it needs, kept in repository secrets. Fetch only public feeds the owner chose. The output is public, so review what the source could publish.

## Stats cards

[github-readme-stats](https://github.com/anuraghazra/github-readme-stats) calls its public instance best-effort and recommends self-hosting. Do this before embedding cards:

1. Deploy your own instance by following that README. Store the token as a host secret, never in the README or the URL.
2. Point the image URLs at your instance.
3. Check each card in both themes and write alt text that states what the card shows.

A card service is a third-party dependency, and a dead one leaves a broken image at the top of a profile.

| Tool | Runs as | Last push | License |
|---|---|---|---|
| [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats) | Hosted service, self-host advised | 2026-10-01 | MIT |
| [vn7n24fzkq/github-profile-summary-cards](https://github.com/vn7n24fzkq/github-profile-summary-cards) | Profile cards | 2026-11-05 | MIT |
| [lowlighter/metrics](https://github.com/lowlighter/metrics) | Profile infographics | 2026-05-29 | MIT |

Cards measure activity, not skill. Offer them when the owner likes them. Do not add them by default.

## Pinned repositories

GitHub lets you [select up to six repositories and gists, combined](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/pinning-items-to-your-profile). The owner sets them in the browser, under Customize your pins.

Choose pins by the audience, and order them by what you want read first:

- Each pin should have a description, a working README and a language that matches the claim. A pin is a promise.
- Prefer finished work over popular forks.
- Pin a repository that would pass `repo-audit`. A hiring reader will open at least one.
- Run this skill on the top pin before polishing the profile. The pin carries more proof than the profile does.

## Who reads it

| Reader | Wants | Looks at | Leave out |
|---|---|---|---|
| Hiring | Evidence of judgment and finished work, what you built, your role in it, and how to reach you | Pins, one or two READMEs, commit messages, the contact link | Skill bars, trophy walls, streaks |
| Followers | What you make, what you are working on now, and where to get more | Recent work, posts, releases | Long career history |
| Maintainers and peers | What you maintain, how you work, and how to contact you | Projects, sponsors, contribution links | Promotional copy |

Choose one primary reader. That choice decides the first line. Step 1 of SKILL.md asks for it.

For hiring, put these first: one line on what you do, two or three projects with what you did and the result, and a contact link. For followers, put current work first and make it live.

## Honest claims

- State only what the owner can show. Each role, project and number links to something real.
- Do not lead with stars. [He et al.](https://arxiv.org/abs/2412.13459) report suspected fake stars at scale, so the number is a weak claim. The abstract page now titles the paper with six million suspected stars, while older copies say 4.5 million.
- Do not use percentage skill bars. They measure nothing.
- Do not use commit streaks or contribution counts as proof of skill. Automation can move them.
- Do not claim ownership of team work. Say what your part was.
- Date anything that ages, such as "as of" for a job or a count. Better, make it live.
- Do not publish private details: home address, phone number, employer internals or client names without permission.

## Checks

- Links resolve, and each image has alt text.
- Images are committed or come from a service you run.
- The page reads well in both themes and on a phone width.
- No image exceeds the proxy limit in [visuals.md](visuals.md#size-limits).
- Score it with [rubric.md](rubric.md). Fit to type means fit to the chosen reader.
