# Moving to InkDesk v0.20.0

v0.20.0 is a complete replacement package. It does not require the individual
0.19.4.x ZIP files and should not be applied through the old ordered incremental
update sequence.

## Repository replacement

Use the supplied `publish-inkdesk-v0.20.0.yml` workflow with
`InkDesk_v0.20.0.zip`. The workflow validates the extracted complete source tree,
creates an optional backup branch, replaces the repository contents, commits the
release and optionally creates tag `v0.20.0`.

## Future versions

Small fixes should use `0.20.1`, `0.20.2` and so on. The next feature release
should use `0.21.0`. Version `1.0.0` remains reserved for a stable release after
cross-browser and real-device validation.
