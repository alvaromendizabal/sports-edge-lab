# Security and private research assets

Do not put credentials, private data, model bodies, active recipes or personal information in a public issue or pull request. If a secret is exposed, revoke or rotate it at its source first, then contact the repository owner through an established private channel. Public deletion alone does not revoke a credential or remove every historical copy.

The project uses synthetic fixtures for public tests and keeps owner execution packages and restricted source observations outside GitHub. See the [publication boundary](docs/PUBLICATION_BOUNDARY.md) for the precise scope. No repository security-reporting feature or third-party audit is claimed unless separately enabled and verified.

Dependency updates should retain meaningful negative tests, provenance checks and chronological admission controls. A green public test suite is not acceptance of a private scientific owner run.
