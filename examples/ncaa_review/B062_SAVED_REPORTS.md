# Reconstruct the saved B062 report

The compact templates restore the exact saved B062 HTML report and notebook using two existing public inputs: the Plotly runtime embedded in the B061 report, and the 3,457-record B060 observed-game census. Both reconstructed files are checked against their byte counts and SHA-256 digests in `B062_REPORT_INTEGRITY.json` before they are written, then read back and checked again.

From the repository root, with these files under `examples/ncaa_review`:

```sh
python examples/ncaa_review/build_b062_saved_reports.py --output-dir examples/ncaa_review
python -m unittest discover -s examples/ncaa_review -p test_b062_saved_reports.py -v
```

Python's standard library is sufficient. The builder defaults to the existing `examples/ncaa_review/B061_EVIDENCE_REPORT.html` and `examples/ncaa_review/data/ncaa_observed_games_b060.json`. Explicit `--base-report`, `--census`, `--template-dir` and `--output-dir` arguments support another checkout layout. `--verify-only` checks reconstruction without writing the large reports.

This operation restores saved reporting outputs. It does **not** execute notebook cells, fit models, fetch provider data, refresh forecasts, advance evidence clocks, or promote a model. The saved notebook retains its original in-process IPython execution record and its explicit lack of an external-kernel execution claim. Rendering the restored report is a separate check.

The `dashboard-browser` CI job also uploads the complete restored HTML and notebook, their integrity record, and browser evidence as the **ncaa-b062-saved-reports** workflow artifact after the render checks pass. This makes the complete outputs available without running the reconstruction command. Hosted artifacts are retained for fourteen days; the committed templates, data and pinned reconstruction remain available afterward.

The `.template.html` and `.template.ipynb` files contain placeholders and are inputs to the builder. Open the reconstructed `B062_EVIDENCE_REPORT.html` and `B062_EVIDENCE_REPORT.ipynb` after the command succeeds. Their bytes match the corresponding `NCAA_B062_EVIDENCE_REPORT` deliverables identified in the integrity file; the public filenames omit the `NCAA_` prefix.

The shared census remains an observed-record inventory with disclosed source gaps, duplicate/alias questions, and separately labeled issued and replay fields. Its 3,457 records are not a certified count of unique games or a complete official universe. Reconstruction does not change those scientific qualifications or create source redistribution rights.
