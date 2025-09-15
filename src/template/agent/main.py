from __future__ import annotations

import argparse
import asyncio
from contextlib import nullcontext
from pathlib import Path
from shutil import copytree

import logfire
from ipdb import launch_ipdb_on_exception
from pydantic_graph import End, Graph
from pydantic_graph.persistence.file import FileStatePersistence

from ..utils import git
from . import nodes
from .config import Settings
from .env import Env
from .state import State


def main():
    """
    Squeeze the external world and distill into the Env fields.
    """
    parser = argparse.ArgumentParser(description="Run me")
    parser.add_argument("--no-logfire", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--restore", metavar="DIR", help="Run path to resume/fork.")
    parser.add_argument("--config")

    # TODO: add more fancy args
    args = parser.parse_args()
    settings = Settings(config_name=args.config)

    logfire.configure(
        send_to_logfire=not args.no_logfire,
        scrubbing=False,
    )
    logfire.instrument_openai()
    # TODO: instrument other stuff like model providers

    branch_name = git.current_branch() or "unknown"
    commit_hash = git.current_commit() or "unknown"
    run_name = f"run-{branch_name}-{commit_hash}"
    run_attrs = {
        # TODO: add run metadata here
    }
    if url := git.github_commit_link(commit_hash):
        run_attrs["github_commit_link"] = url

    # This sets a "resource scope" for the run
    # Things created here would be closed/finalized/cleaned on exit.
    # For example you can't add log entries to that span after leaving this block.
    # But a context manager can be asked to restore the environment to match what the agent previously had.
    with (
        logfire.span(run_name, _span_name="main", **run_attrs) as root,
        (launch_ipdb_on_exception if args.debug else nullcontext)(),
        # TODO: add more resource-managing contexts here
    ):
        # Your unique identifier for this run (make a fresh one for forks)
        run_id = f"{root.context.trace_id:032x}"

        # New runs appear on the bottom, automatically "sorted" by timestamp
        run_path = Path("runs") / Path(run_id)
        run_path.mkdir(exist_ok=True, parents=True)
        logfire.notice(f"Run path: {run_path}")

        if args.restore:
            with logfire.span(f"Restoring from {args.restore}"):
                old_path = Path(args.restore)
                if not old_path.exists():
                    raise Exception(f"Restore path does not exist: {args.restore}")
                if not old_path.is_dir():
                    raise Exception(f"Restore path is not a directory: {args.restore}")
                # XXX: blindly copying the old run path (containing the history file)
                # While this is enough to recover graph state, you may have to write some metadata file
                # to record external resources used like docker image IDs, IPs
                copytree(src=old_path, dst=run_path, dirs_exist_ok=True)

        # TODO: Start the requested services and put their handles here
        deps = Env(
            settings=settings,
            run_path=run_path,
        )
        asyncio.run(agent(deps))


async def agent(deps: Env):
    """
    Prepare and drive the agent loop inside the provided environment.
    """
    # Instantiate the graph
    graph = Graph[State, Env](nodes=nodes.all_nodes)
    start = nodes.Step

    # TODO: You can put more graph-related setup here
    with open(deps.run_path / Path("schema.mmd"), "w") as f:
        f.write(graph.mermaid_code(start_node=start))

    # Initialize the instance
    history_path = deps.run_path / Path("history.json")
    persistence = FileStatePersistence(history_path)
    persistence.set_graph_types(graph)
    if snapshots := await persistence.load_all():
        # TODO: add snapshot filtering like "drop N last steps"
        node, state = None, None
        logfire.debug(f"Loaded {len(snapshots)} snapshots from {history_path}")
        for snapshot in reversed(snapshots):
            if snapshot.kind == "end":
                logfire.debug("Resuming an ended run")
                continue
            if snapshot.kind == "node":
                node = snapshot.node
                if isinstance(node, End):
                    logfire.debug(f"Skipping End node {snapshot.id}")
                    continue
                logfire.debug(f"Restoring from snapshot {snapshot.id}")
                state = snapshot.state
                break
        if node is None or state is None:
            raise RuntimeError(
                f"No viable snapshots in the persistence file {history_path}"
            )
    else:
        node = start()
        state = State()

    await graph.initialize(
        node=node,
        state=state,
        persistence=persistence,
    )

    # Run the graph to completion
    while True:
        async with graph.iter_from_persistence(persistence, deps=deps) as running:
            next = await running.next()
            # TODO: add top-level processing related to the running instance
            logfire.debug(f"Running state: {running.state}")

            # TODO: check the extra termination conditions
            if isinstance(next, End):
                break

        pass  # State snapshot is taken here and recorded in the file


if __name__ == "__main__":
    main()
