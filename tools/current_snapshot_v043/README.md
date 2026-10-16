# current_snapshot_v043

See the dated terminal/schedule evidence; tests do not establish capture success.

Build the self-contained artifact with `python -m zipapp tools/current_snapshot_v043/src -c -o /tmp/current_snapshot_v043.pyz`, then run `python /tmp/current_snapshot_v043.pyz --self-test`. The recorded suite has 32 tests. V043 mocked AWS-client tests need boto3/botocore installed locally; all live credentials remain in the AWS runtime. Never invoke the live entrypoint merely to test it. Code and configuration are retained exactly as deployed.
