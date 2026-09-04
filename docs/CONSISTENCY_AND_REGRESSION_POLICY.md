# Consistency and regression policy

Starting with InkDOS 0.20.1, the project is in refinement and stabilization.

A patch is blocked when it removes an existing function, changes an equivalent control inconsistently between workspaces, leaves public versions and cache identifiers out of sync, or fails any inherited or feature-specific regression test.

Every corrected regression receives a permanent test. New work must preserve Home navigation, local file open/new/save flows, unsaved-change warnings, spreadsheet range selection, formula-reference selection, PDF review/save, TXT editing, EPUB reading, and the established visual system.
