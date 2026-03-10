"""ace cloud — CLI commands for the Kayba hosted API."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

import click

from ace.cli.client import KaybaClient, KaybaAPIError

# Shared options applied to every command in the cloud group.
_api_key_option = click.option(
    "--api-key",
    envvar="KAYBA_API_KEY",
    help="Kayba API key (or set KAYBA_API_KEY).",
)
_base_url_option = click.option(
    "--base-url",
    envvar="KAYBA_API_URL",
    help="API base URL (default: https://use.kayba.ai/api).",
)


def _client(api_key: Optional[str], base_url: Optional[str]) -> KaybaClient:
    """Build a KaybaClient, surfacing auth errors as click failures."""
    try:
        return KaybaClient(api_key=api_key, base_url=base_url)
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))


def _detect_file_type(filename: str) -> str:
    """Infer fileType from extension."""
    ext = Path(filename).suffix.lower()
    return {"md": "md", "json": "json"}.get(ext.lstrip("."), "txt")


# ---------------------------------------------------------------------------
# Top-level group
# ---------------------------------------------------------------------------


@click.group()
def cloud():
    """Interact with the Kayba hosted API."""
    pass


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


@cloud.command()
@click.argument("paths", nargs=-1)
@click.option(
    "--type",
    "file_type",
    type=click.Choice(["md", "json", "txt"]),
    default=None,
    help="Force file type (auto-detected from extension by default).",
)
@_api_key_option
@_base_url_option
def upload(paths, file_type, api_key, base_url):
    """Upload trace files to Kayba.

    PATHS can be files, directories, or '-' for stdin.
    Directories are walked recursively.
    """
    client = _client(api_key, base_url)
    traces = []

    items = list(paths) if paths else ["-"]

    for item in items:
        if item == "-":
            content = sys.stdin.read()
            ft = file_type or "txt"
            traces.append({"filename": "stdin.txt", "content": content, "fileType": ft})
            continue

        p = Path(item)
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file():
                    _add_file(traces, child, file_type)
        elif p.is_file():
            _add_file(traces, p, file_type)
        else:
            click.echo(f"Warning: skipping {item} (not found)", err=True)

    if not traces:
        raise click.ClickException("No traces to upload.")

    try:
        result = client.upload_traces(traces)
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    count = result.get("count", len(result.get("traces", [])))
    click.echo(f"Uploaded {count} trace(s).")
    for t in result.get("traces", []):
        click.echo(f"  {t['id']}  {t['filename']}")


def _add_file(traces: list, path: Path, forced_type: Optional[str]):
    content = path.read_text(encoding="utf-8", errors="replace")
    if len(content) > 350_000:
        click.echo(f"Warning: {path.name} is {len(content)} chars (>350k)", err=True)
    ft = forced_type or _detect_file_type(path.name)
    traces.append({"filename": path.name, "content": content, "fileType": ft})


# ---------------------------------------------------------------------------
# insights
# ---------------------------------------------------------------------------


@cloud.group()
def insights():
    """Generate, list, and triage insights."""
    pass


@insights.command("generate")
@click.option("--traces", "trace_ids", multiple=True, help="Trace IDs to analyze.")
@click.option(
    "--model",
    type=click.Choice(["claude-sonnet-4-6", "claude-opus-4-6"]),
    default=None,
    help="Model to use for analysis.",
)
@click.option("--epochs", type=int, default=None, help="Analysis epochs (default 1).")
@click.option(
    "--reflector-mode",
    type=click.Choice(["recursive", "standard"]),
    default=None,
    help="Reflector mode.",
)
@click.option(
    "--anthropic-key",
    envvar="ANTHROPIC_API_KEY",
    default=None,
    help="Anthropic API key (or set ANTHROPIC_API_KEY).",
)
@click.option("--wait", is_flag=True, help="Poll until the job completes.")
@_api_key_option
@_base_url_option
def insights_generate(
    trace_ids, model, epochs, reflector_mode, anthropic_key, wait, api_key, base_url
):
    """Trigger insight generation from uploaded traces."""
    client = _client(api_key, base_url)
    try:
        result = client.generate_insights(
            trace_ids=list(trace_ids) or None,
            model=model,
            epochs=epochs,
            reflector_mode=reflector_mode,
            anthropic_key=anthropic_key,
        )
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    job_id = result["jobId"]
    click.echo(f"Job started: {job_id}")

    if wait:
        _poll_job(client, job_id)


@insights.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "new", "accepted", "rejected"]),
    default=None,
    help="Filter by review status.",
)
@click.option("--section", default=None, help="Filter by skillbook section.")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@_api_key_option
@_base_url_option
def insights_list(status, section, as_json, api_key, base_url):
    """List insights."""
    client = _client(api_key, base_url)
    try:
        result = client.list_insights(status=status, section=section)
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    items = result.get("insights", [])
    if as_json:
        click.echo(json.dumps(items, indent=2))
        return

    if not items:
        click.echo("No insights found.")
        return

    for ins in items:
        status_str = ins.get("status", "?")
        click.echo(f"  [{status_str:>8}]  {ins['id']}  {ins.get('section', '')}")
        click.echo(f"            {ins.get('content', '')[:120]}")


@insights.command("triage")
@click.option("--accept", "accept_ids", multiple=True, help="Insight IDs to accept.")
@click.option("--reject", "reject_ids", multiple=True, help="Insight IDs to reject.")
@click.option("--accept-all", is_flag=True, help="Accept all pending insights.")
@click.option("--note", default=None, help="Optional triage note.")
@_api_key_option
@_base_url_option
def insights_triage(accept_ids, reject_ids, accept_all, note, api_key, base_url):
    """Accept or reject insights."""
    client = _client(api_key, base_url)

    if accept_all:
        try:
            result = client.list_insights(status="pending")
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))
        accept_ids = tuple(ins["id"] for ins in result.get("insights", []))
        if not accept_ids:
            click.echo("No pending insights to accept.")
            return

    if not accept_ids and not reject_ids:
        raise click.ClickException("Provide --accept, --reject, or --accept-all.")

    errors = []
    for iid in accept_ids:
        try:
            client.triage_insight(iid, "accepted", note=note)
            click.echo(f"  Accepted {iid}")
        except KaybaAPIError as exc:
            errors.append(str(exc))
            click.echo(f"  Error accepting {iid}: {exc}", err=True)

    for iid in reject_ids:
        try:
            client.triage_insight(iid, "rejected", note=note)
            click.echo(f"  Rejected {iid}")
        except KaybaAPIError as exc:
            errors.append(str(exc))
            click.echo(f"  Error rejecting {iid}: {exc}", err=True)

    if errors:
        raise click.ClickException(f"{len(errors)} triage operation(s) failed.")


# ---------------------------------------------------------------------------
# prompts
# ---------------------------------------------------------------------------


@cloud.group()
def prompts():
    """Generate, list, and pull prompts."""
    pass


@prompts.command("generate")
@click.option(
    "--insights", "insight_ids", multiple=True, help="Insight IDs to include."
)
@click.option("--label", default=None, help="Label for the generated prompt.")
@click.option("-o", "--output", "output_path", default=None, help="Save to file.")
@_api_key_option
@_base_url_option
def prompts_generate(insight_ids, label, output_path, api_key, base_url):
    """Generate a prompt from accepted insights."""
    client = _client(api_key, base_url)
    try:
        result = client.generate_prompt(
            insight_ids=list(insight_ids) or None,
            label=label,
        )
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    prompt_id = result.get("promptId", "?")
    version = result.get("version", "?")
    text = result.get("content", {}).get("text", "")

    click.echo(f"Prompt {prompt_id} (v{version}) generated.")

    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        click.echo(f"Saved to {output_path}")
    else:
        click.echo(text)


@prompts.command("list")
@_api_key_option
@_base_url_option
def prompts_list(api_key, base_url):
    """List prompt versions."""
    client = _client(api_key, base_url)
    try:
        result = client.list_prompts()
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    items = result if isinstance(result, list) else result.get("prompts", [])
    if not items:
        click.echo("No prompts found.")
        return

    for p in items:
        pid = p.get("id", p.get("promptId", "?"))
        label = p.get("label", "")
        click.echo(f"  {pid}  {label}")


@prompts.command("pull")
@click.option("--id", "prompt_id", default=None, help="Prompt ID (default: latest).")
@click.option("-o", "--output", "output_path", default=None, help="Save to file.")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@_api_key_option
@_base_url_option
def prompts_pull(prompt_id, output_path, pretty, api_key, base_url):
    """Download a prompt."""
    client = _client(api_key, base_url)

    if prompt_id:
        try:
            result = client.get_prompt(prompt_id)
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))
    else:
        # Get latest by listing and picking first
        try:
            listing = client.list_prompts()
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))
        items = listing if isinstance(listing, list) else listing.get("prompts", [])
        if not items:
            raise click.ClickException("No prompts available.")
        first = items[0]
        pid = first.get("id", first.get("promptId"))
        try:
            result = client.get_prompt(pid)
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))

    text = result.get("content", {}).get("text", "")

    if pretty:
        output = json.dumps(result, indent=2)
    else:
        output = text

    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
        click.echo(f"Saved to {output_path}")
    else:
        click.echo(output)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@cloud.command()
@click.argument("job_id")
@click.option("--wait", is_flag=True, help="Poll until the job completes.")
@click.option(
    "--interval", type=int, default=5, help="Poll interval in seconds (default 5)."
)
@_api_key_option
@_base_url_option
def status(job_id, wait, interval, api_key, base_url):
    """Check the status of an analysis job."""
    client = _client(api_key, base_url)

    if wait:
        _poll_job(client, job_id, interval=interval)
    else:
        try:
            job = client.get_job(job_id)
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))
        _print_job(job)


# ---------------------------------------------------------------------------
# materialize
# ---------------------------------------------------------------------------


@cloud.command()
@click.argument("job_id")
@_api_key_option
@_base_url_option
def materialize(job_id, api_key, base_url):
    """Materialize completed job results into the skillbook."""
    client = _client(api_key, base_url)
    try:
        result = client.materialize_job(job_id)
    except KaybaAPIError as exc:
        raise click.ClickException(str(exc))

    click.echo(
        f"Materialized {result.get('skillsGenerated', '?')} skill(s) "
        f"from job {result.get('jobId', job_id)}."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _poll_job(client: KaybaClient, job_id: str, *, interval: int = 5):
    """Poll a job until it reaches a terminal state."""
    terminal = {"completed", "failed"}
    while True:
        try:
            job = client.get_job(job_id)
        except KaybaAPIError as exc:
            raise click.ClickException(str(exc))

        st = job.get("status", "unknown")
        click.echo(f"  {job_id}  {st}")

        if st in terminal:
            _print_job(job)
            if st == "completed":
                click.echo(f"\nRun: ace cloud materialize {job_id}")
            return

        time.sleep(interval)


def _print_job(job: dict):
    """Pretty-print a job status dict."""
    click.echo(f"Job:    {job.get('jobId', '?')}")
    click.echo(f"Status: {job.get('status', '?')}")
    if job.get("startedAt"):
        click.echo(f"Started: {job['startedAt']}")
    if job.get("completedAt"):
        click.echo(f"Completed: {job['completedAt']}")
    if job.get("error"):
        click.echo(f"Error: {job['error']}")
    result = job.get("result")
    if result:
        click.echo(f"Skills generated: {result.get('skillsGenerated', '?')}")
        if result.get("summary"):
            click.echo(f"Summary: {result['summary']}")
        click.echo(f"Materialized: {result.get('materialized', False)}")
