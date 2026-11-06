# A returned action is not a committed checkpoint

The [credential-free example](checkpoint_commit.py) makes the boundary observable:
an intent is durable before an action starts; its JSON result and a prepared record
binding its stage, byte count and SHA-256 are retained before publication. COMPLETE
appears only after create-only persistence and an independent full-byte readback.
A publication retry verifies the saved result against the original prepared pin
before any remote operation, then consumes that result without running the action
again. Changed bytes are rejected even when they remain valid JSON.

An intent without a saved result is ambiguous and refuses an automatic replay.
The same rule applies if a crash occurs after saving the result but before saving
its prepared record: the example retains the evidence and stops. It never invents
a new pin for unverified surviving bytes or silently repeats an action.

Invented failure cases exercise unavailable persistence, corrupt readback,
encoder rejection, a hard-crash intent, changed saved or committed output, missing
intent/result/prepared records, corrupt or changed identity metadata, unsafe names,
and successful reuse. They run under the existing NBA standard-library test job.
They contain no real games, model fits,
forecasts, licensed responses, private archive identities or cloud paths.

The example is deliberately small. Its caller must provide an exclusive writer
and a durable owned directory. The local pin detects an inconsistent retained
result; it is not a signature or a defense against an actor rewriting the entire
trusted directory. A production recovery system additionally needs
source and attempt binding, authenticated dependency closure, capacity limits,
process locks, bounded retries and durable recovery outside ephemeral scratch.
An independent readback establishes bytes; it does not establish scientific
validity, current coverage, provider rights, an issued prediction or an executed bet.

Historical test receipts remain dated. Passing this example does not retroactively
complete any failed owner run or establish the success of a private successor.
