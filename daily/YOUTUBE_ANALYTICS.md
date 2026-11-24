# YouTube Analytics import

The importer uses Google's YouTube Analytics API with the read-only
`yt-analytics.readonly` scope. It uses only the Python standard library.

## First authorization

Keep the OAuth Desktop client JSON outside this repository and set
`YT_ANALYTICS_CLIENT_JSON` in `.env` to its path (or containing folder). Run:

```sh
python3 daily/youtube_analytics.py authorize --profile en
python3 daily/youtube_analytics.py authorize --profile te
```

Complete Google sign-in and approve the read-only YouTube Analytics scope. Each
profile needs its own authorization because Google asks which YouTube or brand
account to access. Choose the account configured for that profile. Refresh
tokens are saved separately under `~/.config/faceless-shorts/` with owner-only
file permissions. Never commit or share the client or token files.

## Refresh and dashboard

```sh
python3 daily/youtube_analytics.py sync
```

The daily runner refreshes metrics for both authorized profiles after the
broadcast attempt. The Dashboard
Performance tab also has **Sync YouTube Analytics** for an on-demand refresh.
The importer updates views, likes, comments, and average view percentage.
Thumbnail impressions CTR is not imported: YouTube exposes reach metrics through
bulk Reporting API reports rather than this targeted query. Absent metrics are
left as they were rather than treated as zero. Manual Performance tab values are
preserved for any metric the API does not return.

If Google returns `access_denied`, check that the account used for consent owns
or manages the channel and was added as an OAuth test user while the app is in
Testing mode. Reauthorize with `authorize` after changing OAuth settings.
