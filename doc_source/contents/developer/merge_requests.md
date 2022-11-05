# Merge Request Guidelines

1. Use concise, yet informative commit messages
2. Rebase (if you know how) to provide an easy-to-follow history of changes in your branch
3. Update the changelog (`doc_source/contents/developer/changelog.md`) for significant changes
4. Update docs if relevant
5. Add unit tests for any new features
6. Run the unit tests (we use ``pytest``) prior to sending in your changes.

## Commit Messages

Commit messages should begin with a one line concise yet informative summary.
A blank line should separate the one line summary from any additional information.
We strongly recommend using the following templates:

### Commits related to documentation

```
DOCS: [one line description]

[Optional additional information]
```

### Commits fixing bugs

```
FIX: [one line description]

[Optional additional information]
```

## Rebasing

:::{danger}
Rebasing can do permanent damage to your branch if you do not do it correctly.
Practice on a scratch repository until you are comfortable with how rebasing works.
:::

You can use rebasing to clean up the history of commits in a branch to make the changes easier to follow.
Common reasons to rebase include:

* squashing (combining) several closely related commits into a single commit,
* reordering commits, especially to allow squashing, and
* dropping (removing) commits related to debugging.
