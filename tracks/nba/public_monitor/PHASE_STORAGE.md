# Phase storage admission and stable workspace identity

This NBA example uses invented quantities and identities to explain a storage
decision. It contains a pure calculation and failure-case tests. It does not
inspect or mutate a real filesystem, acquire data, execute models, or interact
with another process.

A fixed minimum free-space threshold can pass while the next phase still lacks
room. Account for all allocations that coexist at each phase: unpacked runtime,
required restored files, checkpoint growth, outputs, temporary writes and a
retained reserve. The maximum phase allocation determines initial admission.
Keep measured inputs distinguishable from estimates for future growth.

The [example implementation](phase_storage.py) makes four decisions explicit:

1. Keep room for the eventual return and control evidence on the home volume,
   even if new working files use another volume.
2. Compare device identities. Two directory labels on the same filesystem do
   not supply two independent pools of free space. When observations disagree,
   use the smaller reported free capacity for that shared device.
3. Bind a selected private workspace to its project, build, volume and principal.
   A missing workspace requires authenticated recovery; a replacement or
   symlink cannot silently become a continuation of the previous workspace.
4. Recheck space before new writes. Sparse files created with `truncate` may not
   consume physical storage yet, so their unfilled bytes still count against
   the next admission decision. Verified existing files require no new copy.

These checks complement memory, CPU and concurrency limits. A storage decision
does not authorize changing those limits, deleting unrelated files or operating
another process. A free-space observation is not a reservation: concurrent
activity can consume capacity after a check, and a real implementation must
retain partial evidence and report failure truthfully.

## Run the synthetic tests

From the repository root:

```bash
python -m unittest discover -s tracks/nba/public_monitor/tests -p 'test_phase_storage.py' -v
```

The [tests](tests/test_phase_storage.py) cover insufficient phase capacity,
independent volume selection, shared-device aliases, return reserve, private
restart binding, missing workspaces and cumulative sparse allocations. All
numbers are small fictional examples. They make no claim about actual NBA game
coverage, private runtime capacity, research results or cloud CI execution.
