---
name: github_repo
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [repo]
outputs: [items, found, repo]
side_effect: false
---
# github_repo

Returns metadata of ONE GitHub repository in ONE request: stars, forks, open
issues, language, license, topics, last push, archived flag.

- `repo="owner/name"` (or a github.com URL) -> `GET /repos/{owner}/{name}`.
  This is the stable path: 60 req/hour without a token.
- `repo="langchain"` (bare name) -> `GET /search/repositories?q=langchain in:name`,
  exact repo name preferred. Search is limited to 10 req/min without a token.
  Not sorted by stars: that returned the wrong repo (microsoft/markitdown).
- `404` -> `found=false`. Rate limit -> error dict telling the agent to set
  `GITHUB_TOKEN` or pass `owner/name`.
- Optional `GITHUB_TOKEN` env var raises the limit to 5000 req/hour.

Use it for "repo X bao nhiêu star / còn được maintain không / license gì".
It is NOT for reading README or code (use `fetch` with the repo URL).
