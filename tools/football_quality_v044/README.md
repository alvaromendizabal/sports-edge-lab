# football_quality_v044

Failed before AWS client construction/provider network; retained unchanged for reproducibility. Use v045.

Build the self-contained artifact with `python -m zipapp tools/football_quality_v044/src -c -o /tmp/football_quality_v044.pyz`, then run `python /tmp/football_quality_v044.pyz --self-test`. The recorded suite has 73 tests. V043 mocked AWS-client tests need boto3/botocore installed locally; all live credentials remain in the AWS runtime. Never invoke the live entrypoint merely to test it. Code and configuration are retained exactly as deployed.
