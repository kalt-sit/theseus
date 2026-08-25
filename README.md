# Theseus

> Theseus supports curious builders on safer journeys. It audits third-party agent skills before installation, keeps untrusted content separate from trusted instructions, and works without an external model or runtime service.

Theseus is a portable, read-only security review skill for the [Agent Skills](https://agentskills.io/) format. It inventories the whole candidate package, examines execution, downloads, permissions, persistence, secrets, and external-content exposure, then returns an evidence-based PASS, CONDITIONAL, or REJECT decision.

## Why Theseus

Agent skills combine natural-language instructions with scripts and resources. Reviewing only `SKILL.md`, trusting a registry badge, or running setup steps during inspection can miss the actual risk. Theseus makes the review boundary explicit:

- candidate content is data, never trusted authority;
- inspection is static and read-only;
- every file must be accounted for;
- installation and configuration are separate user decisions;
- popularity and automated audits are supporting signals, not substitutes for evidence.

## Use cases

- Review a third-party skill before installation.
- Compare an update with the previously approved revision.
- Investigate a registry warning or unexpected capability.
- Produce a cited audit report for a team decision.
- Identify host permissions and network access before approval.

## Install

```bash
DISABLE_TELEMETRY=1 npx skills@1.5.23 add 'kalt-sit/theseus#v2.0.0' --skill theseus -g -a hermes-agent --copy -y
```

The command pins both the Skills CLI and the Theseus release tag, and disables the CLI's anonymous install telemetry. Before installation, review the tagged `skills/theseus/` package; afterward, confirm that the copied package matches that tagged directory. Theseus itself does not send telemetry, call an external model, install helper tools, or modify host configuration.

## Package boundary

The installable skill is intentionally small:

```text
skills/theseus/
├── SKILL.md
└── references/
    └── audit-checklist.md
```

Historical machine-specific operations, installer recipes, hooks, scheduled jobs, and local record paths are not part of the public skill package.

## Migrating from v1

Version 2 is intentionally a smaller, host-independent security core. It removes the v1 host automation, integrity-monitoring script, local trust records, and harness-specific setup guides. If you rely on those operations, keep v1 pinned until you have replaced them with a separately maintained local adapter. Installing v2 does not replace active monitoring.

## Compatibility

The core guidance is host-independent and requires no network access or code execution. A compatible host only needs to read the skill and inspect candidate files. Platform-specific installation behavior belongs to the chosen Agent Skills client, not Theseus.

## Host guides

- [Hermes Agent](docs/hosts/hermes.md)
- [Codex](docs/hosts/codex.md)

These guides explain discovery, audit requests, expected results, and host permission boundaries. They do not add host automation to the installable Core.

## Development

Run the distribution contract tests with the Python standard library:

```bash
python3 -m unittest discover -s tests -v
```

The tests enforce the package allowlist, portable frontmatter, read-only contract, link integrity, and absence of known high-risk scanner triggers from the installable package.

## Security

See [SECURITY.md](SECURITY.md) for the threat model and private reporting route. Theseus reduces review risk but cannot prove that opaque, encrypted, dynamically downloaded, or mutable artifacts are safe.

## Japanese

日本語の案内は [README.ja.md](README.ja.md) にあります。

## License

MIT
