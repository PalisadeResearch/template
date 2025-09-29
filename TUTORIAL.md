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
> ```js
> // those are inline annotations
> // the actual field wouldn't have those
> ```

```js
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
> ```js
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

To test the waters, drop this code into a main.py somewhere at the top:

```python
import logfire
from contextlib import contextmanager

@contextmanager
def env():
    with logfire.span("The scope"):
        logfire.info("TODO: Setup")
        try:
            yield "hey"  # The value that gets captured in the `with .. as ..` block.
        finally:
            logfire.info("TODO: Cleanup")
```

Then plug it into the `main` function:

```python
        with (
            nullcontext(),  # Placeholder
            # TODO: Start the requested services
            env() as hey,
        ):
            logfire.notice(f"Hey, {hey}")
            # raise Exception("oh no")
```

Now, if you re-run agent using `agent --no-logfire --no-git smoke`, you'll see the new log entries (note the order and indentation):

```
16:48:04.727 run-tutorial-85be8b17
16:48:04.803   Run path: runs/0199812190f7a3fa76b3a5227c9aafa2
16:48:04.805   The scope
16:48:04.805     TODO: Setup
16:48:04.806     Hey, hey
16:48:04.824     run graph graph
16:48:04.825       run node Step
16:48:04.828         1: example
...
16:48:04.859     run graph graph
16:48:04.860       run node Step
16:48:04.861         5: example
16:48:04.865     TODO: Cleanup
```

Uncommenting `raise Exception` will short-circuit the run, but not the setup/cleanup:

```
17:07:41.830 run-tutorial-85be8b17
17:07:41.909   Run path: runs/0199813387068da7fbac1daccfd374e9
17:07:41.910   The scope
17:07:41.910     TODO: Setup
17:07:41.911     Hey, hey
17:07:41.911     TODO: Cleanup
Traceback (most recent call last):
...
```

Since "The scope" is nested inside the `run-tutorial-...`, it has access to the directory of the run (`runs/01998...`).
We can pass that path to the context manager and and log the result:

```python
        with (
            env(run_path) as hey,
        ):
            logfire.notice(f"Hey, {hey}")
            hey.write("Hey!\n")
```

Let's use the provided run_path to open (and close!) a file handle:

```python
import logfire
from pathlib import Path

from contextlib import contextmanager


@contextmanager
def env(run_path: Path):
    with logfire.span("The scope"):
        fp = run_path / Path("hey.txt")
        logfire.info(f"Opening {fp}")
        f = open(fp, "a")  # Will create file explicitly just for the demo...
        try:
            yield f  # This handle is valid only inside the with-block
        finally:
            logfire.info(f"Closing {fp}")
            f.close()  # ... and close it too.
```

Running `agent smoke --no-logfire --no-git` you now should see the resulting file path and a handle to it in the logs:

 ```
12:24:09.116 run-tutorial-8500a265
12:24:09.196   Run path: runs/019994c95f1cce9b35b0097433bd1255
12:24:09.197   The scope
12:24:09.197     Opening runs/019994c95f1cce9b35b0097433bd1255/hey.txt
12:24:09.198     Hey, <_io.TextIOWrapper name='runs/019994c95f1cce9b35b0097433bd1255/hey.txt' mode='a' encoding='UTF-8'>
12:24:09.213     run graph graph
12:24:09.214       run node Step
12:24:09.217         1: example
...
12:24:09.239     run graph graph
12:24:09.239       run node Step
12:24:09.241         5: example
12:24:09.245     Closing runs/019994c95f1cce9b35b0097433bd1255/hey.txt
```

The file should contain the "Hey!" line resulting from the `hey.write()`.

Now you can see the `--restore` argument in action.
Run `agent smoke --no-logfire --no-git --restore runs/019994c95f1cce9b35b0097433bd1255` (with a run path of your own):

```
12:33:47.068 run-tutorial-8500a265
12:33:47.116   Run path: runs/019994d230bc7c9a083dd1560c4dcdc6
12:33:47.117   Restoring from runs/019994c95f1cce9b35b0097433bd1255
12:33:47.119   The scope
12:33:47.119     Opening runs/019994d230bc7c9a083dd1560c4dcdc6/hey.txt
12:33:47.120     Hey, <_io.TextIOWrapper name='runs/019994d230bc7c9a083dd1560c4dcdc6/hey.txt' mode='a' encoding='UTF-8'>
12:33:47.134     run graph graph
12:33:47.135       run node Step
12:33:47.137         5: example
12:33:47.141     Closing runs/019994d230bc7c9a083dd1560c4dcdc6/hey.txt
```

A few things to notice:

1. The run is short - it starts at "step 5" and immediately finishes.
  That means the persisted graph state did carry over.
2. The old run ID only shows up in the "Restoring from ..." line.
  The previous run is "finalized" and you can't "log more entries into it".
  The run that resulted from the restoration is effectively forked from its parent and has an isolated history.

Divining into the files will reveal a few more details:

1. Inspecting the new `hey.txt` file will now show two "Hey!" lines.
2. Its [metadata](./runs/019994d230bc7c9a083dd1560c4dcdc6/metadata.json) file has the single entry in its `ancestors`field, pointing to the run it were restored from.

Let's register that handle in then `Env` class so it would be available in the run.

Go to the [Env.py](./src/tutorial/agent/env.py) and add a new field to the `Env` class:

> The readme has a default value here, so we have to add our new field before it for Env constructors to work smoothly.

```python
    # TODO: add handles and capabilities here
    hey: "io.TextIOWrapper"

    readme: str = "example"
```

Then pass the actual handle to the Env in `main.py`:

```python
            deps = Env(
                settings=settings,
                run_path=run_path,
                # TODO: Put service handles here
                hey=hey,
            )
```

Finally, let's pick the handle from the node context and use it:

Edit the `Step.run()` in [nodes.py](src/tutorial/agent/nodes.py):

```python
        # Mutate the state (persisted in the history file)
        ctx.state.changeme += 1

        # Perform IO in the world using a handle
        ctx.deps.hey.write(f"Hello from Step. changeme={ctx.state.changeme}\n")
```

Run `agent --no-logfire --no-git smoke` again and inspect its new `hey.txt` file.

It will contain the data from the node:

```
Hey!
Hello from Step. changeme=1
Hello from Step. changeme=2
Hello from Step. changeme=3
Hello from Step. changeme=4
Hello from Step. changeme=5
```

Re-run with `--restore` from the last path and you'll see an extra section in its file:

```
...
Hello from Step. changeme=4
Hello from Step. changeme=5
Hey!
Hello from Step. changeme=5
```

Finally, let's tie that with the metadata tracking to simulate dynamic-but-persistent configuration.

In a real configuration that can be map of network ranges or live container IDs.
Here we will use the file once more to go through the checklist for the "initialize or restore" pattern.

First, go to the [Env.py](./src/tutorial/agent/env.py) and add a new field to the `Metadata` class:

```python
    # TODO: add more things to preseve and track across runs
    hey_name: str
```

Now, fill in the field when creating the metadata record:

```python
                # TODO: Register more env-related metadata here
                hey_name=str(Path(hey.name).relative_to(run_path)),
```

> A relative path is used to prevent names pointing back at the original runs.
> It is better to keep the forked runs standalone if you can.
> Otherwise you'd have to resolve the conflicts and updates between the different runs.

Adapt the context manager to only append the default file name if it given a directory:

```python
@contextmanager
def env(fp: Path):
    with logfire.span("The scope"):
        if fp.is_dir():
            fp = fp / Path("hey.txt")
        # the rest is the same
        logfire.info(f"Opening {fp}")
        ...
```

Now we can pass a file path if we have one from the metadata of a previous run.
Replace the run_path arg with a conditional too:

```python
        with (
            nullcontext(),  # Placeholder
            # TODO: Start the requested services
            env(
                run_path / Path(old_meta.hey_name) if old_meta else run_path,
            ) as hey,
        ):
```

To test the setup we'll to some workspace and metadata surgery:

1. Do an initial run: `agent --no-logfire --no-git smoke | grep "Run path:"`
2. Rename the `hey.txt` in its path to `hola.txt`
3. Edit the `metadata.json` file and update `hey_name` path to `hola.txt`.

Restore the modified run and see that the new non-default environment gets picked up correctly:

```
15:19:42.026 run-tutorial-84cecf9e
15:19:42.055   Run path: runs/0199956a174abb8cb31891e142a92345
15:19:42.056   Restoring from runs/019995699bfd64536061fc247176f4fd
15:19:42.058   The scope
15:19:42.058     Opening runs/0199956a174abb8cb31891e142a92345/hola.txt
15:19:42.059     Hey, <_io.TextIOWrapper name='runs/0199956a174abb8cb31891e142a92345/hola.txt' mode='a' encoding='UTF-8'>
15:19:42.074     run graph graph
15:19:42.075       run node Step
15:19:42.078         5: example
15:19:42.083     Closing runs/0199956a174abb8cb31891e142a92345/hola.txt
```

In a realistic setup that would mean that e.g. your contnainers and network IPs got the values that match the agent's state.

Now you're equipped with an ability to encode your setup to recover from failures and explore alternative trajectories.
