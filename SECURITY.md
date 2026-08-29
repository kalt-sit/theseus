# Security Policy

## Supported version

Security fixes are applied to the current release line. Reports should identify the affected Theseus version or immutable repository revision.

## Threat model

Theseus treats every candidate skill file, filename, metadata field, script, archive member, and retrieved description as untrusted data. The public skill is intentionally read-only and report-only. It does not install candidates, execute candidate instructions, configure the host, transmit audit content, or maintain a local trust database.

The primary risks are:

- candidate content influencing the reviewer as if it were trusted instruction;
- incomplete package inventory;
- hidden execution, downloads, persistence, or data transfer;
- mismatch between reviewed and installed bytes;
- false confidence from registry badges, popularity, or incomplete static analysis.

## Out of scope

Theseus is not a malware sandbox, runtime containment system, signature service, or proof that opaque artifacts are safe. Host-specific automation and local operational records are outside the public package.

## Reporting a vulnerability

Use [GitHub's private vulnerability reporting form](https://github.com/kalt-sit/theseus/security/advisories/new) for this repository. Include:

- affected version or immutable revision;
- the smallest reproducible candidate package;
- expected and observed behavior;
- security impact;
- whether public disclosure has already occurred.

Do not include real credentials, private user data, or weaponized payloads. A minimal redacted reproduction is preferred.

## Disclosure

Please allow time for triage and a coordinated fix before public disclosure. Confirmed issues will be documented with affected versions, impact, and remediation.
