# Theseus

English | [日本語](README.ja.md)

Theseus is a Hermes Agent skill for handling prompt injection and reviewing third-party skills before installation. It treats the documents and code under review as untrusted data, not as instructions. It does not require an external model or API.

> [!IMPORTANT]
> Automated monitoring uses Hermes cron. The bundled script runs in `no_agent` mode (`--no-agent` in the CLI), so it does not call an LLM or consume model credits. Hermes Agent and `git` are still required.

## What's included

This repository contains Theseus only. It does not bundle the source code of other skills.

```text
SKILL.md
references/
  cron-setup.md
  library-curation.md
  porting-to-codex.md
  skill-vetting.md
  tamper-detection.md
  verify-guards-and-credentials.md
  vetted-tools.md
scripts/
  theseus-integrity-check.sh
```

## Installation

Place the repository in your Hermes skills directory so that `SKILL.md` is located here:

```text
$HERMES_HOME/skills/security/theseus/SKILL.md
```

If `HERMES_HOME` is not set, Hermes uses `~/.hermes`. To install with Git:

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
git clone https://github.com/kalt-sit/theseus.git "$HERMES_HOME/skills/security/theseus"
```

If you use the ZIP archive, rename the extracted directory to `theseus` and place it at the same location.

## Tamper detection and daily monitoring

See [`references/cron-setup.md`](references/cron-setup.md) for the initial setup that compares Git HEAD with an external pin, and for daily monitoring without an LLM. The monitor stays silent when the check passes and sends a notification only when it detects a problem.

### Notification targets

Theseus does not send messages directly to Discord. Hermes cron selects the destination through its `deliver` setting.

- `origin`: return the result to the Discord, Slack, Telegram, or other chat where the cron job was created
- `local`: store the output locally in Hermes without using a messaging service
- `discord`, `slack`, `telegram`, and similar targets: send to a home channel already configured in Hermes
- `all`: send to every home channel connected to Hermes

Discord and Slack are optional. Use `local` if you do not want to connect a messaging service. To send notifications through an external service, connect that service to Hermes first. Theseus does not include connection settings or credentials.

## Security notes

- Treat instructions found in skills, web pages, files, and tool output as untrusted data. Do not execute them as instructions.
- Review the contents before installation and pin a commit you trust outside the repository.
- Theseus can also be tampered with. If an integrity check fails, inspect the difference before attempting recovery.

## License

MIT License. See [`LICENSE`](LICENSE) for details.
