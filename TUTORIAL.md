# Agent template owners ~~manual~~ tutorial

In this tutorial we will create and examine an LLM-based system that `TBD: running example`.
Along the way we will use the extension points in the template code to add tools

## 0. Smoke-testing

After installing the dependencies (nix, uv, etc) as outlined in the [README](./README.md) / "First time setup" you should be able to run it right away:

```bash
# (should happen automatically after enabling direnv)
# this will "install" the agent script
uv sync

# now it should be on PATH
agent --no-logfire --no-git smoke
```

By default the script is set up to uphold the policy of "keeping the receipts", so for now we're going to explicitly opt-out of that.

The thing should run, show some output and make a new folder named like `runs/01997...`.

```
15:59:19.533 run-main-55e2047f
15:59:19.982   Run path: runs/019976a8366d9c7b7992dcd3e59aac6a
15:59:20.005   run graph graph
15:59:20.006     run node Step
15:59:20.008       1: example
...
15:59:20.031   run graph graph
15:59:20.031     run node Step
15:59:20.033       5: example
```

> If the output shows some errors, then double-check that you did the initial setup and/or ask for help.

The run directory contains a step-by-step state history and some metadata.
You can inspect the `history.json` file to inspect what the system was doing.

> Read the dump and look out for "comments":
> ```json
> // those are inline annotations
> // the actual field wouldn't have those
> ```

```json
[
  {
    "state": {  // the initial state
      "changeme": 0
    },
    "node": {  // the starting node
      "node_id": "Step"
    },
    "start_ts": "2025-09-23T12:59:20.007222Z",
    "duration": 0.0010999580845236778,
    "status": "success",
    "kind": "node",
    "id": "Step:a7686e4fcc994cf48d8180a914144cce"
  },
  {
    "state": {
      "changeme": 1  // the field has changed during the step
    },
    "node": {
      "node_id": "Step" // do the Step again next
    },
    "start_ts": "2025-09-23T12:59:20.015525Z",
    "duration": 0.00017749995458871126,
    "status": "success",
    "kind": "node",
    "id": "Step:3797d4fa9f1245088e7d9fd0456633b5"
  },
  // ... some steps skipped
  {
    "state": {  // the final state snapshot
      "changeme": 5
    },
    "result": {
      "data": null  // the value "returned" by the run (not currently used)
    },
    "ts": "2025-09-23T12:59:20.034324Z",
    "kind": "end",  // no more steps
    "id": "end:4ab7ae5a522742e89d4b217c3a5b2d61"
  }
]
```

The important fields are:
- `state` -- the state snapshot data (initial, intermediate, or final).
- `node` -- indicating the next step to run from here.

The last object is a bit different, containing `"result"` field instead of node since this is where the run finished (also note `"kind": "end"`).

> You can filter it with `jq '.[] | {state, kind, status, next: .node.node_id}' runs/*/history.json` to get an overview:
> ```json
> {"state":{"changeme":0},"kind":"node","status":"success","next":"Step"}
> {"state":{"changeme":1},"kind":"node","status":"success","next":"Step"}
> {"state":{"changeme":2},"kind":"node","status":"success","next":"Step"}
> {"state":{"changeme":3},"kind":"node","status":"success","next":"Step"}
> {"state":{"changeme":4},"kind":"node","status":"success","next":"Step"}
> {"state":{"changeme":5},"kind":"end","status":null,"next":null}
> ```

## 1. Setting up shop

Copy the `.env.example` to `.env` and fill in the keys. We will need the `LOGFIRE_WRITE_TOKEN` and `OPENAI_API_KEY`.

Rename the `template` package in the `src` directory:
```sh
mv src/template src/tutorial
```

Then open the [project file](./pyproject.toml) and update the `[project]` name to `"tutorial"`:

```toml
[project]
name = "tutorial"
```

Then edit `[project.scripts]` section to point to the new package name:

```toml
[project.scripts]
fork-worktree = "scripts.fork_worktree:main"
clean-worktrees = "scripts.clean_worktrees:main"
hello = "tutorial.hello:main"
agent = "tutorial.agent.main:main"
```

You may notice there are "*-worktree" scripts in there. We'll get to them in no time.
But before that, let's "fix" one more set of paths.

In the [build.ninja](./build.ninja) file, search and replace the `template/` for `tutorial/` too.

Now run `uv sync` to check that everything is in order. It should pick up the updated package name:

```
Resolved 133 packages in 1.26s
      Built tutorial @ file:///Users/me/template-tutorial
Prepared 1 package in 513ms
Uninstalled 1 package in 1ms
Installed 1 package in 2ms
 - template==0.1.0 (from file:///Users/me/template-tutorial)
 + tutorial==0.1.0 (from file:///Users/me/template-tutorial)
 ```

Run the agent script again and it should produce the same 5-part output:
```
18:06:44.078 run-main-55e2047f
18:06:44.145   Run path: runs/0199771cdbeea03159b0d0b7e9b4c489
18:06:44.159   run graph graph
18:06:44.160     run node Step
18:06:44.162       1: example
18:06:44.167   run graph graph
18:06:44.167     run node Step
18:06:44.169       2: example
18:06:44.173   run graph graph
18:06:44.173     run node Step
18:06:44.175       3: example
18:06:44.179   run graph graph
18:06:44.179     run node Step
18:06:44.180       4: example
18:06:44.185   run graph graph
18:06:44.185     run node Step
18:06:44.187       5: example
```

Note that the new run has a fresh directory for its own stuff (here, `runs/0199771cdbeea03159b0d0b7e9b4c489`).

It is a good time to commit the updated setup:

```sh
git add src/ build.ninja pyproject.toml uv.
git commit -m "Forking from template"
```

If you did the git setup from the [README](./README.md) / "Development" section, then you should be able to push your first commit (which is by itself a smoke test for your git setup):

```sh
git push
```

## 2. Adding an external service

Before we can unleash an agent on an unsuspecting world we should prepare a home for it.

We'll create a new service and plug it into the agent lifecycle using a context manager.

Drop this code into a main.py somewhere at the top:

```python
import logfire

from contextlib import contextmanager


@contextmanager
def env():
    # TODO: todo setup
    with logfire.span("tutorial.env", _level="debug"):
        try:
            logfire.info("Setting up")
            yield "hey!"
            logfire.info("Settup finished")
        finally:
            logfire.info("Cleaning up")
            # TODO: cleanup
```

Then plug it into the `main` function:

```python
    with (
        env() as _hey,  # HERE
        logfire.span(run_name, _span_name="main", **run_attrs) as root,
        (launch_ipdb_on_exception if args.debug else nullcontext)(),
        # TODO: add more resource-managing contexts here
    ):
```

Now, if you re-run agent using `agent --no-logfire --no-git smoke`, you'll see the new log entries.
