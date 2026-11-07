# History rewrite playbook

Read this in step 7, or in step 2 if the audit found a secret, before anything else touches the repository.

**This playbook has not been run end to end.** Nothing was force pushed, and git-filter-repo was not installed when it was written. It comes from [GitHub's sensitive data guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), the [git-filter-repo manual](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt) and inference. Marked "inferred" where it goes past them. Go slowly and keep the backup.

Most cases stop at step 1. Every step past step 2 waits for the owner's explicit yes.

Set `R=owner/repo` and `B=default-branch` first.

## Why this rarely finishes the job

- GitHub says old commits stay reachable by SHA in cached views, through PR refs, and in forks and clones.
- The public `activity` endpoint gives anyone the `before` SHA of a force push. It returned those SHAs to a non-admin caller on `ossf/scorecard` on 2026-11-06. A cleanup force push therefore points any reader at the commit that holds the secret (inferred).

```bash
gh api "repos/$R/activity?activity_type=force_push&ref=$B&per_page=100"
```

How long that feed keeps entries is unverified. So is how long GitHub keeps cached views.

## Step 1. Rotate before anything else

If the data is a secret, revoke or rotate it first. GitHub and git-filter-repo both say this, and both say rotation may be enough. A rewrite without rotation protects nothing, because the value is already exposed (inferred). Record proof of rotation. Never paste the value anywhere.

Ask in order:

1. Was the repository ever public, or was the secret ever pushed? Then treat it as compromised forever (inferred).
2. Is the secret dead? Then rewriting usually is not worth the damage.
3. Is the data not a credential, such as personal data or a license problem? Rotation does not help, so a rewrite may be justified (inferred).
4. Is this only about size? GitHub Support will not remove non-sensitive data, so a size rewrite may not shrink server storage or remove old objects (inferred, and unverified). Consider a fresh repository with an archived original.

## Step 2. Inventory the blast radius

Read-only. Save the output.

```bash
gh pr list -R $R --state open --limit 1000 --json number,headRefName
gh api "repos/$R/forks?per_page=100" --paginate --jq '.[].full_name'
gh release list -R $R --limit 1000 --json tagName,isDraft
gh api repos/$R/immutable-releases --jq .enabled
gh api repos/$R/rulesets --jq '.[]|[.id,.name,.target,.enforcement]|@tsv'
git for-each-ref --format='%(refname) %(objecttype)' refs/tags
git ls-files ':(attr:filter=lfs)'
```

List what a rewrite cannot reach. All inferred except where marked:

- The wiki is a separate `.wiki.git` repository.
- Uploaded release assets, Actions logs, artifacts, caches and Packages stay.
- Text quoted in issues, PR bodies and comments stays. GitHub says dereferencing does not remove it.
- Other repositories that pin your SHAs break, including `.git-blame-ignore-revs`, submodule pointers and action pins.
- Public mirrors and archives outside GitHub are out of reach.

## Step 3. Get approval and freeze

Show the owner the inventory and get an explicit yes. Tell every collaborator the window, and ask them to stop pushing. Concurrent work is otherwise lost or forces a redo. Merge or close open PRs, because comments on old diffs can be lost.

## Step 4. Back up

```bash
git clone --mirror https://github.com/$R.git backup.git
git -C backup.git bundle create ../backup.bundle --all
git -C backup.git bundle verify ../backup.bundle
```

`git bundle verify` needs a repository, so run it through `-C`. Run `git lfs fetch --all` in the mirror if LFS is used.

The backup contains the sensitive data. Keep it encrypted and offline, give it an owner and a deletion date, and delete it after the retention window (inferred).

## Step 5. Rewrite in a fresh clone

Install git-filter-repo 2.47 or newer, which added `--sensitive-data-removal`. Call it as an external tool. Work in a fresh clone, because the fetch step can discard local-only changes. Keep the replacement file outside the repository.

```bash
git clone https://github.com/$R.git work && cd work
git-filter-repo --sensitive-data-removal --invert-paths --path path/to/file
git-filter-repo --sensitive-data-removal --replace-text ../replacements.txt
```

The two commands are separate uses. Repeat runs are supported and extend the first run.

- Name every historical path of the file, including renames.
- `--sensitive-data-removal` fetches all refs, so refs outside branches and tags are cleaned too.
- It removes commit and tag signatures, including on commits before the sensitive one. Expect a verified history to become unverified.

Use BFG only if you have a reason. GitHub's page no longer mentions it, it cannot clean protected commits, and [it leaves HEAD alone by default](https://rtyley.github.io/bfg-repo-cleaner/). [Git's docs](https://git-scm.com/docs/git-filter-branch) point to git-filter-repo in place of `filter-branch`.

## Step 6. Verify locally. This is the last exit

```bash
git log --all --name-status -- path/to/file
git log -S'string-to-check' --all --format=%h --name-only
grep -c '^refs/pull/.*/head$' .git/filter-repo/changed-refs
cat .git/filter-repo/first-changed-commits
```

GitHub's example uses `-p` for the string search. Leave it out, so the secret does not print. Rerun gitleaks if you have it. If the PR count is larger than expected, discard this clone. Past the next step the rewrite is irreversible.

## Step 7. Open the gates narrowly

Record the current rules first:

```bash
for i in $(gh api repos/$R/rulesets --jq '.[].id'); do gh api repos/$R/rulesets/$i > ruleset-$i.before.json; done
gh api repos/$R/branches/$B/protection > protection.before.json
```

Expect these to block the push:

- A force push block rejects it.
- A required signatures rule rejects the rewritten unsigned commits, because filter-repo strips signatures (inferred).
- A tag rule can block rewritten tags (inferred).
- A tag tied to an immutable release cannot move or be deleted while the release exists. Deleting the release frees the tag for deletion, and the tag name stays unusable. That tag keeps the bad commit reachable until you do so (inferred). Check this in step 2 and plan for the burned name.

Prefer a temporary bypass for one named actor over disabling the rule (inferred).

## Step 8. Force push

This is the irreversible step. It needs the owner's yes for this exact command.

```bash
git push --force --mirror origin
```

What it does:

- Overwrites every ref and discards anything pushed since you started.
- Pushes to `refs/pull/*` fail. GitHub marks them read-only, so that is expected.
- Any other failure usually means protection is still on.
- With `--no-fetch`, `--mirror` can delete refs you never fetched.
- Open PRs change diffs, and closed PR diffs break, including later PRs built on this history.
- The `activity` feed exposes the old SHA to anyone.

Restore every rule from step 7 at once, then diff against the saved JSON.

## Step 9. Forks and GitHub Support

Forks keep the commit. You must ask fork owners to clean or delete their forks, and GitHub cannot give you their contact details.

[GitHub Support](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) acts only if rotation cannot mitigate the risk, and only after all refs except PRs are clean and no fork holds the data. It will not remove non-sensitive data.

Give Support the owner and repository, the affected PR count, the First Changed Commits, and the orphaned LFS file if the tool reported one. Support may then delete or dereference PRs, run garbage collection, remove cached views and purge orphaned LFS objects. Deleting a PR removes its conversation. Dereferencing keeps text but loses the diff.

Contacting Support is an external message, so the owner sends it.

## Step 10. Clean other clones

The simple instruction is to delete and reclone. Otherwise each person:

1. Deletes all tags, then runs `git fetch --prune --tags`.
2. Rebases work onto the new history.
3. Runs `git reflog expire --expire=now --all` and `git gc --prune=now`. Stash entries are lost here.
4. Confirms with `git cat-file -t <first-changed-commit>`, which must fail for each commit.

Three rules prevent recontamination:

- Collaborators rebase, never merge. One merge can bring back the tainted history.
- A stale `git pull` followed by `git push` also brings it back.
- Do not run filter-repo again in each clone. It can produce different hashes.

## Step 11. Verify on the server, in two stages

GitHub will not let you rewrite `refs/pull/*`, so PR refs keep old commits until Support acts. Check each stage for what it can prove.

**After the force push, before Support.** A plain clone gets heads and tags only, so the first changed commit must be gone from it. A mirror also fetches `refs/pull/*`, so hits there are expected and any other hit is a miss.

```bash
git clone https://github.com/$R.git plain
git -C plain cat-file -t <first-changed-commit>
git clone --mirror https://github.com/$R.git verify.git
git -C verify.git for-each-ref --contains <first-changed-commit> | grep -v 'refs/pull/'
```

The `cat-file` call must fail, and the last command must print nothing (inferred). The API still returns the commit at this stage, so a 200 is not a failure.

**After Support finishes.** The API call should now fail, and a fresh mirror should be clean.

```bash
gh api repos/$R/commits/<first-changed-commit>
git clone --mirror https://github.com/$R.git verify2.git
git -C verify2.git cat-file -t <first-changed-commit>
```

The "No commit found for SHA" response shape was seen only on a nonexistent SHA, never after a real purge. A 200 at this stage means the object is still reachable or cached (inferred).

## Step 12. Prevent repeats

- Add the path to `.gitignore`.
- Turn on push protection and a pre-commit secret scan, from [guards.md](guards.md).
- Watch for the first changed commit returning. Few forges can ban a commit, so monitor it.
- Delete the backup on its date.
- Record what rotated and when.
- Give collaborators the reclone instructions.

## Sources

All read 2026-11-06. The `activity` result and the `git bundle verify` behavior were measured that day.

- [Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), [git-filter-repo manual](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/), [git-filter-branch](https://git-scm.com/docs/git-filter-branch)
- [Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
