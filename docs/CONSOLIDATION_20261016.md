# Consolidation record — 2026-10-16 UTC

The canonical deployment uses one repository, one SageMaker Studio space and one private S3 bucket for five internal sports tracks.

## Verified final state

| Resource | Verified state |
| --- | --- |
| Repository | `alvaromendizabal/sports-edge-lab`; full original NFL history retained |
| Development space | `sports-edge-lab-dev`, InService configuration, 150 GiB EBS |
| Development instance | `ml.m7i.2xlarge`, 8 vCPUs, 32 GiB, CPU image 4.5.2 |
| Idle shutdown | 60 minutes |
| Notebook application | Stopped after configuration; acquisition runs in Processing jobs |
| Data lake | `sagemaker-sports-edge-lab-560403859723-us-west-2`, private and encrypted |
| Sport prefixes | `tracks/nfl/`, `tracks/nba/`, `tracks/ncaaf/`, `tracks/ncaam/`, `tracks/ncaaw/` |

The five temporary per-sport spaces and the original `nfl-edge-lab-dev` space were removed after preserving the old home. The six former Sports Edge Lab buckets were removed after a successful central archive verification and a final unchanged-source manifest check. Unrelated projects were not changed.

## Archive verification

The migration verified **1,663 source objects totaling 1,451,136,208 bytes**. This includes both the original legacy NFL archive and its track copy, plus metadata and receipts. It must not be described as 1,663 unique sports datasets. The original pinned NFL asset scope remains **815 files totaling 722,613,027 bytes**.

Object checks covered byte length and metadata. Where multipart upload semantics made ETags incomparable, streamed SHA-256 hashes were compared instead. An earlier attempt incorrectly assumed equivalent ETags; another encountered stream API compatibility. Both were repaired before the final successful verification. Source data was retained until the repaired verification completed.

The final migration receipt is private at:

`infrastructure/migrations/consolidation_20261016.json`

The [migration source](../tools/consolidate_archive.py) is a historical one-time utility. Its old source buckets no longer exist; it should not be rerun as the normal ingestion entry point.

## Legacy home backup

The original space home was archived and independently verified before deletion: **124 files, 753,256 original bytes**. Verification included archive download, SHA-256 and reading every archive member.

Private archive:

`infrastructure/legacy-space-backups/nfl-edge-lab-dev-20261016T0034Z/home.tar.gz`

SHA-256:

`f66dbd742864b7e73c76852f47007155bca9df2204f7c50d702dee7218f68072`

An independent verification receipt is stored alongside it. Cache, runtime and log directories were excluded. The temporary backup application and lifecycle configuration were removed after verification.

## Acquisition remains a separate gate

Consolidation proves preservation and relocation of existing records. It does not establish complete historical coverage, successful modeling or market profitability. Provider canaries and bounded backfills are recorded separately in acquisition receipts.
