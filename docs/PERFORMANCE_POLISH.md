# Performance polish — 2026-09-25

Baseline: `adfd0ee125573ddfbc4adf4c62aac91a5c7ecebf` (main read from GitHub, not an earlier checkpoint).

## Diagnostic and intervention plan

Preserve the six independent local-first workspaces, synchronous launch capture,
transactional import, validation, source safety and complete offline snapshots.
Make no version/release changes. Measure before choosing further interventions.

1. **Snapshot infrastructure:** verified local reuse into a separate new cache;
   fetch only cache misses/hash mismatches; drain the concurrent batch before
   deleting a failed candidate; retain native waiting/activation cleanup.
   Validate clean install, one-file update, tamper repair, network rejection,
   partial rollback, old-version availability, offline, scope and waiting.
2. **Presentations:** measure a synthetic shared-layout/master/theme/image deck;
   cache immutable decoded package resources only within each decode operation.
   Retain serial slide order and transactional commit unless measurements justify
   the added complexity of concurrency/progressive import. Verify counters,
   output equivalence, editing, navigation, history and preservation round-trip.
3. **All workspaces:** measure empty startup and synthetic file opening in fresh
   browser contexts; preserve the PDF first-render-before-tools changes. Change
   critical-path loading only for demonstrated benefit, then run exact candidate
   and behavioral audits for Chromium, Firefox and WebKit.

## Confirmed observations before changes

The shell contains 266 resources / 4,255,712 bytes. The real worker runtime under
the deterministic CacheStorage/network harness downloads all 266 resources on
a one-file update: 4,255,733 bytes for the synthetic replacement. There are 266
SHA-256 calls. This establishes redundant network work, **not** device latency.

Each launch runtime is 3,676 bytes. Its top-level work defines helpers, registers
the consumer and exports the API; picker/DataTransfer work runs on demand.
No timing evidence currently justifies splitting this reliable early capture.

PPTX source inspection shows repeated layout/master/theme relationship and XML
reads and repeated image decompression. Browser counters must quantify this.

The baseline PDF component smoke suite fails in
`tests/test_pdf_stability_offline_contract.py`: it reads the absent legacy
`.github/workflows/stability-freeze-regression.yml`. This pre-existing failure
must not be silently omitted or weakened.

## Snapshot comparison

Run from the candidate root:

```sh
INKDOS_BENCHMARK_ONLY=1 node tests/test_offline_snapshot_incremental.cjs ../baseline/service-worker.js
INKDOS_BENCHMARK_ONLY=1 node tests/test_offline_snapshot_incremental.cjs
node tests/test_offline_snapshot_incremental.cjs
```

| One-file update | Baseline | Candidate |
| --- | ---: | ---: |
| Network requests | 266 | 1 |
| Network body bytes | 4,255,733 | 9,891 |
| SHA-256 calls | 266 | 267 |
| Resources written to new snapshot | 266 | 266 |

Unchanged assets remain hashed and copied, preserving independent snapshots;
CPU hashing and cache-write costs are **not eliminated**. The extra hash is the
changed old resource, rejected locally before verifying its replacement.
The expected reduction in update contention on XeOS needs real-device testing.
No timing/RAM/battery gain is claimed from these structural counts.
