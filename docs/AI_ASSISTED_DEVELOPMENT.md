# AI-Assisted Development Policy

AI-assisted code is allowed, but it is not accepted as evidence that a change is correct.

## Required for AI-assisted changes

- State that AI materially assisted the change in the pull request.
- Explain the intended behavior in the contributor's own words.
- Identify the files and data structures affected.
- Add or update a regression test when feasible.
- Run the full quality gate.
- Manually test the changed workflow in a browser.
- Remove speculative abstractions, empty bridges and unused code.

## Prohibited patterns

- claiming support that was not tested;
- adding native/platform bridges that contain only placeholders;
- copying proprietary code, fonts or documents;
- accepting generated code solely because it looks plausible;
- combining unrelated refactors and new features in one pull request;
- silently swallowing parser errors to make a test appear successful.

## Review approach

Reviewers should prefer small, explicit code over generated architectural layers. A smaller fix with a reproducible test is more valuable than a broad compatibility claim.
