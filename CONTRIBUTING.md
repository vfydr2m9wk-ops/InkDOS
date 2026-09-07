# Contributing

Keep app runtimes independent. Do not centralize duplicated runtime code merely to reduce bytes.

A change to a frozen app requires a new app revision and its own regression gate. Suite-level integration may not mutate another app as a side effect.
