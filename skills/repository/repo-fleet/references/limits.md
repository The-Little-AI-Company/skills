# GitHub limits for fleet work

Read this before a scan of more than a few hundred repositories, before planning ring size, and whenever GitHub returns a 403, 429 or 502.

Sources were read on 2026-11-06. Measurements come from one session against public owners, so treat them as a starting point.

## Budgets

| Limit | Value | Source |
|---|---|---|
| GraphQL primary | 5,000 points per hour per user. Apps vary | [GraphQL limits][graphql] |
| GraphQL secondary | 2,000 points per minute. A query costs 1 point, a mutation 5 | [GraphQL limits][graphql], [REST limits][rest] |
| REST secondary | 900 points per minute. A read costs 1, a write 5 | [REST limits][rest] |
| Concurrency | At most 100 concurrent requests, shared across REST and GraphQL | [REST limits][rest] |
| CPU | 90 seconds of CPU per 60 seconds of real time, at most 60 of it GraphQL | [REST limits][rest] |
| Content creation | About 80 requests per minute and 500 per hour. Some endpoints are lower | [REST limits][rest] |
| Request timeout | 10 seconds. A timeout costs extra points in the next hour | [GraphQL limits][graphql] |
| Connection size | `first` must be 1 to 100, with a ceiling of 500,000 nodes per call | [GraphQL limits][graphql] |

Fleet pull request volume is bounded by the content creation limit, not by the hourly quota.

## Page size

Use a page size of 50, not 100. The connection allows 100, but a nested inventory query stopped working there.

| Page size | Time | Result | Cost |
|---|---|---|---|
| 25 | 4.3 s | ok | 1 |
| 50 | 5.7 s | ok | 2 |
| 100 | 11.4 s | HTTP 502 | not reported |

That table is one sample each, against the `ossf` organization.

## What a page may ask for

The number of lookups per repository matters as much as the page size. All of these ran at page size 50, twice each, on `ossf` and on `sindresorhus`.

| Lookups per repository | Time | Result |
|---|---|---|
| No file lookups | 3 to 5 s | 4 of 4 ok |
| 11 `object()` lookups, one per path | 10 to 13 s | 3 of 4 returned HTTP 502 |
| 15 `object()` lookups, one per path | 9 to 12 s | 2 of 4 returned HTTP 502 |
| 3 `object()` tree lookups: root, `.github`, `docs` | 6 to 9 s | 4 of 4 ok |

Each `object()` path adds git lookups for every repository on the page, and the query sits near the 10 second limit. Fetch the three folder listings and match names in the client. That also catches `README.rst`, `LICENSE-MIT` and lowercase template names. `fleet_scan.py` does this, and it read all 85 `ossf` repositories in 14 seconds for 2 points.

Heavier fields such as `checkSuites` and CODEOWNERS errors also returned 502 at page size 100. Leave them out of the inventory query, and fetch them for the repositories that need them.

## Reads

- Scan with GraphQL first. Use REST only for the repositories that need it. At 12 REST calls per repository, a 5,000 per hour budget covers about 400 repositories an hour (inference from the budget above).
- Make requests one at a time ([best practices][practices]).
- Order the scan by name, not by push date. A push during the scan moves a repository between pages under `PUSHED_AT` (opinion).
- Set `ownerAffiliations: [OWNER]` so the list holds owned repositories only. What this argument defaults to on a user account was not checked, so always pass it.
- Avoid code search for targeting. It hit a rate limit after about 12 calls in a minute.

## Writes

- Wait at least 1 second between mutating requests. That is GitHub's floor for large batches ([best practices][practices]).
- Space pull requests at least 30 seconds apart. This is opinion, chosen to protect shared CI.
- A pull request with labels and reviewers takes about 3 content-creating calls. At one every 30 seconds that is about 360 calls an hour, under the 500 ceiling (inference).
- Treat 500 per hour as the hard cap for a campaign, including comments, labels and review requests.

## When a limit trips

Check these in order ([best practices][practices]).

| Signal | Action |
|---|---|
| `retry-after` header is present | Wait that many seconds before the next request |
| `x-ratelimit-remaining` is `0` | Wait until `x-ratelimit-reset`, which is UTC epoch seconds |
| Rate limit error with neither header | Wait at least 1 minute. If it repeats, double the wait each time |
| Retries keep failing | Stop with an error after a fixed number of attempts |
| HTTP 502 or a timeout on a read | Retry the same cursor at a smaller page size. Stay at that size |
| Second secondary limit in a ring | Stop the ring and report. This is a SKILL.md stop rule |

Never keep sending requests while limited. GitHub warns that this can get the integration banned ([best practices][practices]).

`fleet_scan.py` applies this table. It steps through page sizes 50, 25 and 10, gives up after 5 retries, and stops rather than wait more than 15 minutes for one limit. It writes what it read, with `complete` set to false, and exits 1. The attempt count, the wait cap and the pause below 100 remaining points are opinion.

`fleet_track.py` backs off on a rate limit and counts each secondary limit it sees against the ring of the row it was reading. It cannot see limits your campaign tool hit. Read that tool's log and pass the count with `--secondary-hits RING=COUNT`.

[graphql]: https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
[rest]: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
[practices]: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
