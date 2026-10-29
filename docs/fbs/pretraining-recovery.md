# Verified pretraining checkpoints

This portable example extracts two reusable ideas from a source-inventory recovery fix. It contains no owner paths, account identifiers, credentials, production executable hashes, or provider integrations.

`pretraining_recovery_denial` expresses a strict eligibility contract: explicit exact-run selection, verified process/source/lock identity, every thread stopped, a final source-inventory STARTED event, and zero optimizer or completed-fit markers. Recheck this evidence after a potentially long checkpoint copy. An earlier successful check becomes stale if another controller resumes the process or the scientific phase advances. This policy helper does not identify or signal any process.

`checkpoint_inactive_delete_catalog` provides a smaller operation that needs no process signals. It acquires the existing writer flock normally or refuses immediately, preserves the database and possible rollback journal, and opens a separate copy for SQLite crash recovery. It closes the connection before hashing the recovered database, verifies SQLite integrity, syncs files and directories, and writes an explicit completion receipt. Every writer must use the same existing lock file. Deleting or replacing that file invalidates the coordination contract.

A recovered catalog is provisional evidence. Its receipt does not claim that source discovery completed or that absent objects do not exist. Fresh reconciliation is required before asserting absence. Existing fit files are outside this example and are never changed.

Run the six local tests from the repository root:

```sh
python3 -m unittest examples.fbs_contracts.tests.test_pretraining_checkpoint -v
```

The tests launch invented local child processes. One child exits deliberately with an unfinished SQLite transaction, leaving a real hot rollback journal. The test verifies that the original database and journal remain byte-identical, the recovered copy contains only committed rows, and a held real flock prevents checkpointing. These checks demonstrate checkpoint mechanics; they are not scientific training or validation results.

Primary references: [SQLite atomic commit](https://sqlite.org/atomiccommit.html), [SQLite corruption prevention](https://sqlite.org/howtocorrupt.html), and [Python SQLite connection context managers](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager).
