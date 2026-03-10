"""ACE Framework CLI."""

import click

from ace.cli.cloud import cloud


@click.group()
@click.version_option(package_name="ace-framework")
def cli():
    """ACE Framework CLI."""
    pass


cli.add_command(cloud)


def main():
    cli()
