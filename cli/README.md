# Products CLI — Assignment

Build a command-line tool that talks to the Products API in [`../server`](../server).
This folder (`cli/`) is where you implement your solution. You are free to
**modify the server too** if your approach calls for it — just explain what you
changed and why.

> **Unfamiliar with a term** (API, endpoint, access/refresh token, stdout, ...)?
> See the plain-English glossary in the [top-level README](../README.md#key-concepts--terminology).
> It's fine to learn as you go and use AI assistants — but don't use them blindly:
> we may discuss your solution in a technical interview, so make sure you fully
> understand it and the trade-offs of your approach.

> **⚠️ Your submission is checked by an automated validator.** It runs your CLI
> and asserts specific acceptance criteria against the contract declared in this
> README: the exact command names, options, JSON output shapes, exit codes, and
> the auth/refresh behaviour described below. **Follow the declared API to the
> letter** — deviations (different command names, extra prompts on stdout,
> wrapped or reformatted JSON, non-zero exits on success) will fail the checks.
> Where this README does **not** explicitly specify something, you are free to
> come up with your own solution — use your judgement and be ready to explain your choices.

## How to approach this (suggested order)

1. **Run the server** (below) and open `http://localhost:8000/docs` — this is an
   interactive page where you can try every endpoint in the browser. Click
   `POST /auth/login`, "Try it out", log in with `demo` / `password123`, and
   see the tokens you get back.
2. **Get `login` working** in the CLI: call `/auth/login`, save the returned
   tokens (and the base URL) to a file on disk.
3. **Get `products list` working**: read the saved token, send it in the
   `Authorization: Bearer <token>` header, print the JSON response.
4. **Add the refresh flow**: when a request comes back `401`, call
   `/auth/refresh`, save the new tokens, and retry. (See the walkthrough below.)
5. **Add filters, `get`, `update`, and `batch-update`.**

> Start simple and get one command fully working before moving on.

## Getting started (uv)

This project is managed with [uv](https://docs.astral.sh/uv/).

```bash
cd cli
uv sync            # create the virtualenv and install dependencies
uv run products-cli --help
```

Add dependencies as you need them, e.g. `uv add typer` or `uv add rich`.
An HTTP client (`httpx`) is already included. The CLI entry point is `main()` in
[`src/products_cli/__init__.py`](src/products_cli/__init__.py), exposed as the
`products-cli` command.

## Run the server first

From the repository root:

```bash
docker compose up --build
# or
cd server && uv run uvicorn app.main:app --port 8000
```

API base URL: `http://localhost:8000` · Interactive docs: `/docs` ·
Demo user: `demo` / `password123`.

## Required API

Your CLI consumes the following endpoints. Authenticated requests use the header
`Authorization: Bearer <access_token>`.

### Auth

| Method | Path            | Body                        | Response                                   |
|--------|-----------------|-----------------------------|--------------------------------------------|
| POST   | `/auth/login`   | `{username, password}`      | `{access_token, refresh_token, token_type}`|
| POST   | `/auth/refresh` | `{refresh_token}`           | `{access_token, refresh_token, token_type}`|

**Token refresh — important.** An access token is only valid for a limited number
of authenticated requests (20) **and** a limited lifetime (60 seconds by default).
When either is exceeded the API returns **HTTP 401**. When this
happens your CLI must use the stored refresh token to obtain a new token pair via
`/auth/refresh`, then transparently retry the request. Refresh tokens are rotated,
so always persist the newest pair. Because each CLI invocation is a separate
process, you must **persist tokens to disk** between commands.

> Every authenticated response also carries `X-Token-Requests-Used`,
> `X-Token-Requests-Limit`, and `X-Token-Expires-At` headers describing the
> token's remaining budget — handy if you want to refresh before hitting a 401.

In plain steps, every authenticated command should:

1. Read the saved access token from disk and send it in the
   `Authorization: Bearer <access_token>` header.
2. If the response is **not** `401`, use it as normal.
3. If it **is** `401`, POST the saved refresh token to `/auth/refresh` to get a
   new `{access_token, refresh_token}` pair, **save both to disk**, and retry the
   original request once with the new access token.

> "Transparently" means the user never sees this happen — they just run the command
> and it works, even on the 21st call.

### Products

| Method | Path               | Purpose                                       |
|--------|--------------------|-----------------------------------------------|
| GET    | `/products`        | list products (query filters below)           |
| GET    | `/products/{id}`   | get one product                               |
| POST   | `/products`        | create a product                              |
| PATCH  | `/products/{id}`   | update fields of one product                  |
| DELETE | `/products/{id}`   | delete a product                              |

A product has: `id, name, section, description, discount, price`.

`GET /products` query parameters: `section`, `name` (case-insensitive substring),
`min_price`, `max_price`, `has_discount` (bool), `limit`, `offset`.

> **Response shape:** `GET /products` returns a paginated envelope, not a bare
> array: `{"items": [...], "pagination": {"limit", "offset", "count", "total"}}`.
> Your `products list` command should still print the products (extract `items`).

> **Note:** there is intentionally **no bulk/batch endpoint**. The `batch-update`
> CLI command still has to work — decide how to implement it (e.g. fetch the
> matching products and update them one by one, or add your own endpoint to the
> server). Explain your choice.

## Required CLI commands

Implement at least the following. Data commands should print **valid JSON** to
stdout and exit `0` on success; on error, print a message to stderr and exit
non-zero.

The **API base URL is provided at authentication time** via a required
`--base-url` option on `login`. Persist it alongside the tokens so subsequent
commands reuse it without passing it again.

```
products-cli login --base-url <url> --username <u> --password <p>
    Authenticate against the given API URL and store the base URL + token pair.
    --base-url is required. Prints {"status": "ok"}.

products-cli products list [--section S] [--name TEXT] [--min-price N]
                           [--max-price N] [--has-discount | --no-discount]
                           [--limit N] [--offset N]
    Prints a JSON array of products. Uses the stored base URL.

products-cli products get --id <id>
    Prints a single product as JSON.

products-cli products update --id <id> [--name ...] [--section ...]
                             [--description ...] [--discount N] [--price N]
    Updates the given fields; prints the updated product as JSON.

products-cli products create --name <name> --section <section> --price <N>
                             [--description ...] [--discount N]
    Creates a product; prints the created product as JSON.

products-cli products delete --id <id>
    Deletes the given product. Prints {"status": "ok"}.

products-cli products batch-update --section <section> --discount <N>
    Sets discount for every product in the section (there is no batch endpoint
    — you choose how). Prints {"updated": <count>}.
```

The `products *` commands must **not** require `--base-url`; they read it from
what `login` stored. (You may accept an optional `--base-url` override if you
like.)

## Constraints & expectations

- Language: **Python**, managed with **uv**.
- Handle the token-refresh flow: a run that makes more than 20 authenticated
  requests must still succeed.
- Support the listed `list` filters.
- Implement `batch-update` however you see fit — the server has no batch endpoint,
  so either update matching products individually or add your own endpoint.
- Keep tokens out of version control (store the base URL and tokens under the
  user's home or a git-ignored path).
- You may modify the server; if you do, note what and why.
- Update this README with any run instructions specific to your implementation.

## Evaluation criteria

Part of the evaluation is **automated**: a validator exercises your CLI and
checks the acceptance criteria implied by the declared API above (command names,
options, JSON shapes, exit codes, refresh-on-401). Anything not explicitly
declared here is up to you — pick a reasonable approach and explain it.

| Area                    | What we look for                                            |
|-------------------------|------------------------------------------------------------|
| Correctness             | Commands behave as specified; JSON output is valid.        |
| Auth & refresh handling | Tokens persisted; automatic refresh + retry on 401.        |
| Filtering               | `list` filters map correctly to API query params.          |
| Batch update            | `batch-update` works; approach is sound and explained.     |
| Code quality            | Clear structure, error handling, readable code.            |
| Docs                    | README lets us install and run without guesswork.          |

## Suggested time budget

The **coding itself** is meant to take **around 3 hours** — it's intentionally
small, so don't overcomplicate it. **Time spent learning and setting up doesn't
count** and won't be held against you: if uv, HTTP APIs, or the auth/refresh flow
are new to you, take the time you need to read the docs and get comfortable. We
care about the result and your reasoning, not the clock.

If you're short on time, prioritise `login`, `products list` (with filters), and
the refresh flow.
