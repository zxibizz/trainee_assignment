# Products CLI Challenge

A take-home assignment: build a command-line tool that talks to a provided
Products API.

> **New to some of this? That's expected.** You don't need to already know every
> tool or term used here. Everything is explained below in plain language, with
> links to the official docs, and you're encouraged to use AI assistants to fill
> any gaps. If you can read a doc page and ask good questions, you can do this.

> **In one sentence:** there's a small web server (the "API") that stores products;
> you'll write a program you run in the terminal (the "CLI") that logs in to that
> server and lists/updates products.

## Layout

| Path        | Purpose                                                              |
|-------------|---------------------------------------------------------------------|
| `server/`   | Reference API service (auth, products CRUD). You may modify it if needed. |
| `cli/`      | Where you build the CLI. Start with [`cli/README.md`](cli/README.md).      |
| `docker-compose.yml` | One-command way to run the server.                         |

## The task

Build a Python CLI (managed with [uv](https://docs.astral.sh/uv/)) that:

1. **Authenticates** against the API and stores the returned tokens. Access tokens
   expire after 20 authenticated requests, so the CLI must **refresh transparently**
   on `HTTP 401`.
2. **Lists products** with filters (section, name, price range, discount).
3. **Updates products** — a single product by id, and many at once by filter
   (set the discount for a whole section).

Full details and the required API/CLI contract are in
[`cli/README.md`](cli/README.md).

## Time & expectations

- The **coding** is meant to take **around 3 hours**. It is intentionally small
  — **don't overcomplicate it**. A clean, working solution beats an elaborate one.
- **Learning and setup time doesn't count.** If some tools or concepts here are
  new, take the time you need to read the docs — that's expected and won't be
  held against you. We care about the result and your reasoning, not the clock.
- **Using AI assistants (Copilot, ChatGPT, etc.) is completely fine** — use
  whatever helps you work. But **don't use it blindly**: we may walk through your
  solution together in a technical interview, so be ready to explain how it works
  and the **pros and cons** of the approach you chose.

## Prerequisites

You'll need the following installed. If you haven't used **uv** before, don't
worry — it's a fast Python package/environment manager and the only slightly
unusual tool here; the install command below is all you need.

| Tool       | Version | Why                                      | Install                                                                 |
|------------|---------|------------------------------------------|-------------------------------------------------------------------------|
| **Python** | 3.10+   | Runs the server and your CLI.            | [python.org/downloads](https://www.python.org/downloads/) (uv can also install it for you) |
| **uv**     | latest  | Manages dependencies & virtualenvs.      | [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | latest  | Optional — run the server in one command.| [docs.docker.com/get-started](https://docs.docker.com/get-started/get-docker/) |

Docker is only needed if you prefer `docker compose up` over running the server
with uv.

## Running the server

```bash
docker compose up --build
# or, with uv:
cd server && uv run uvicorn app.main:app --port 8000
```

API base URL: `http://localhost:8000` · Docs: `/docs` · Demo user: `demo` / `password123`.

## Building the CLI

```bash
cd cli
uv sync
uv run products-cli --help
```

See [`cli/README.md`](cli/README.md) for the required commands and evaluation
criteria.

## Submitting your solution

When you're done, package the repository into a single archive and email it to
HR — no public GitHub repo required. Run this from the repository root (only
Python 3 is needed, so it works on Windows, macOS, and Linux):

```bash
python package_submission.py "Your Name"
```

This creates `products-cli-challenge-<your-name>-<timestamp>.tar.gz` in the current
directory. It automatically leaves out generated/local-only files (virtualenvs,
caches, the SQLite database, git history, stored tokens), so only your source
and docs are shipped. Use `--output-dir <dir>` to write the archive elsewhere.

## Key concepts & terminology

> If any of these are new, skim the linked page (a few minutes each) or ask an AI
> assistant to explain — that's part of the exercise.

| Term | Plain-English meaning | Learn more |
|------|-----------------------|------------|
| **API** | A web server you talk to over HTTP instead of a UI. You send requests, it sends back data (here, as JSON). | [What is a REST API?](https://developer.mozilla.org/en-US/docs/Glossary/REST) |
| **HTTP request / method** | How you talk to an API. `GET` reads data, `POST` creates, `PATCH` updates, `DELETE` removes. | [HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) |
| **Endpoint** | A specific URL path on the API, e.g. `/products` or `/auth/login`. | [FastAPI docs](https://fastapi.tiangolo.com/) |
| **JSON** | The text format the API uses for data: `{"name": "Mouse", "price": 25}`. | [Working with JSON](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON) |
| **CLI** | "Command-line interface" — a program you run in the terminal with commands and flags, e.g. `products-cli products list --section books`. | [Typer](https://typer.tiangolo.com/) / [argparse](https://docs.python.org/3/library/argparse.html) |
| **Access token** | A short-lived string proving you're logged in. You send it on every request in the `Authorization` header. | [Bearer tokens](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication) |
| **Refresh token** | A longer-lived string used to get a new access token when the old one stops working (here, after 20 requests). | [OAuth refresh tokens](https://www.oauth.com/oauth2-servers/making-authenticated-requests/refreshing-an-access-token/) |
| **401 Unauthorized** | The HTTP status the API returns when your access token is missing/expired — your cue to refresh and retry. | [401 status](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/401) |
| **stdout / stderr** | The two output streams of a program: normal results go to stdout, error messages to stderr. | [Standard streams](https://en.wikipedia.org/wiki/Standard_streams) |
| **Environment variable** | A value set in your shell that programs can read, e.g. a config path. | [uv & env](https://docs.astral.sh/uv/) |
| **HTTP client** | A library your code uses to make requests. `httpx` is already installed for you. | [httpx docs](https://www.python-httpx.org/) |

## Server configuration (env vars)

| Variable                  | Default | Meaning                                        |
|---------------------------|---------|------------------------------------------------|
| `MAX_REQUESTS_PER_TOKEN`  | `20`    | Authenticated requests allowed per access token.|
| `ACCESS_TOKEN_TTL_SECONDS`| `60`    | Access-token lifetime (seconds) before expiry.  |
| `REFRESH_TOKEN_TTL_SECONDS`| `3600` | Refresh-token lifetime (seconds) before re-login.|
| `DOWNSTREAM_EVENT_BUS_LATENCY_SECONDS`| `0.4`   | Round-trip latency (s) of publishing a mutation to the downstream event bus / audit log (writes only). |
| `DATABASE_PATH`           | `products.db` | SQLite file location.                     |
| `JWT_SECRET`              | dev value | HMAC secret for JWTs.                         |
