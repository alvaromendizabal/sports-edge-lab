# Bounded output checkpoint example

An operation can finish successfully while its accumulated result no longer
fits a single checkpoint envelope. Increasing the envelope limit conceals the
growth and can make recovery exceed memory or storage limits.

The credential-free [example](bounded_checkpoint.py) writes an immutable returned
sequence in bounded JSON-record shards. Each descriptor binds sequence position,
record count, byte count and SHA-256. A compact manifest binds the complete
ordered payload. Every shard and the manifest receive create-only publication
and an independent full readback before a reference is returned.

```bash
python -m unittest tracks.nba.public_monitor.tests.test_bounded_checkpoint -v
```

All test events are invented. A partial publication can be resumed from the
same immutable returned output without invoking its producer. Existing exact
objects may be reused, but this example grants no new computation credit.
An unknown action outcome remains unresolved; storage recovery cannot establish
that a producer finished or authorize its repetition.

The tests cover oversized individual records, multi-shard restoration, partial
publication, independent-readback corruption, scratch-free remote recovery,
missing or altered bodies, reordered or omitted descriptors, repeated equal
content at distinct sequence positions, unknown manifest fields and capacity
limits. A valid prefix is never returned as a complete restored result.

This teaching implementation intentionally limits total restoration size and
validates the full sequence before exposing rows. It contains no network client,
process locking, private path codec, model, cloud location or actual run record.
Production consumers additionally need admitted ownership, authenticated source
and attempt identity, physical dependency closure, durable operation journals,
and a verified spool or equivalent transaction boundary for larger streams.

The [stage commitment example](CHECKPOINT_COMMIT.md) explains the separate action,
prepared-output, publication, commit and acknowledgement states. Software tests
of either example establish neither an actual owner completion nor model gains.
