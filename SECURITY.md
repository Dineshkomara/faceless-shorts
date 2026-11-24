# Security policy

Do not commit OAuth client-secret files, refresh tokens, provider keys, `.env`, local channel history, or private render assets. Use environment variables or a secret manager for credentials. Keep the dashboard bound to `127.0.0.1`; it has no authentication layer and should not be exposed to a public network.

Zapier publishing requires the video and cover to be uploaded to a public file host first. This is disabled unless ALLOW_PUBLIC_FILE_HOSTING=1 is set. Review the selected host's retention policy and never enable this for private or unreleased media.

If a credential is accidentally committed, revoke it at its provider before removing it from repository history. Report security issues privately to the repository maintainer rather than opening a public issue with secrets or account details.
