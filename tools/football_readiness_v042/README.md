# football_readiness_v042

See the dated terminal/schedule evidence; tests do not establish capture success.

Build the self-contained artifact with `python -m zipapp tools/football_readiness_v042/src -c -o /tmp/football_readiness_v042.pyz`, then run `python /tmp/football_readiness_v042.pyz --self-test`. The recorded suite has 59 tests. V043 mocked AWS-client tests need boto3/botocore installed locally; all live credentials remain in the AWS runtime. Never invoke the live entrypoint merely to test it. Code and configuration are retained exactly as deployed.
