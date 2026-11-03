## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues (Hamza-339/shop-assistant), using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Git workflow

### Branches

Create a branch per ticket: `feat/<n>-slug`, where `<n>` is the GitHub issue number and `slug` is a short kebab-case descriptor of the work.

Example: `feat/42-add-cart-persistence`

### Commits

Commit after each red/green/refactor cycle (TDD discipline):

- **Red**: failing test commit
- **Green**: implementation commit that passes the test
- **Refactor**: cleanup and optimization commits

Use [conventional commits](https://www.conventionalcommits.org/) with the ticket number in parentheses:

```
feat(auth): add login form (#42)
test(auth): add login validation test (#42)
refactor(auth): extract session logic to hook (#42)
```

Format: `<type>(<scope>): <description> (#<n>)`

Common types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.
