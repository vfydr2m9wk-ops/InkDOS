# Historical migration to InkDesk 0.20.0

InkDesk 0.20.0 was originally published as a complete source replacement. That
historical process is no longer the normal update mechanism.

Starting with 0.20.1, maintenance releases use the stable incremental workflow
at `.github/workflows/apply-inkdesk-update.yml` and root
`InkDesk-update-v*.zip` packages. Workflow files are installed manually and are
not self-modified by update packages.
