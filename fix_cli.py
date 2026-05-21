import os
import re

filepath = "bist_signal_bot/cli/commands.py"
with open(filepath, "r") as f:
    content = f.read()

if "def review():" not in content:
    review_command = """

import json
from .formatting import format_json

@click.group()
def review():
    \"\"\"Analyst Review Inbox and Manual Research\"\"\"
    pass

@review.command()
@click.option('--status', help="Filter by status")
@click.option('--symbol', help="Filter by symbol")
@click.option('--json', 'as_json', is_flag=True, help="Output as JSON")
def inbox(status, symbol, as_json):
    \"\"\"Show analyst review inbox\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager
    manager = create_review_inbox_manager()
    items = manager.list_items()

    # Simple filtering
    if status:
        items = [i for i in items if i.status.value == status]
    if symbol:
        items = [i for i in items if i.symbol == symbol.upper()]

    if as_json:
        data = [i.summary() for i in items]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Analyst Review Inbox")
        for item in items:
            click.echo(f"[{item.item_id[:8]}] {item.symbol} - {item.status.value}")

@review.command()
@click.argument('item_id')
@click.option('--evidence', is_flag=True, help="Include evidence")
@click.option('--json', 'as_json', is_flag=True, help="Output as JSON")
def show(item_id, evidence, as_json):
    \"\"\"Show details of a review item\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager
    manager = create_review_inbox_manager()
    item = manager.get_item(item_id)
    if not item:
        click.echo(f"Item {item_id} not found.")
        return

    if as_json:
        click.echo(json.dumps(item.safe_public_dict(), indent=2))
    else:
        from bist_signal_bot.review.reporting import format_review_item_text
        click.echo(format_review_item_text(item))

@review.command()
@click.option('--symbol', required=True)
@click.option('--title', required=True)
@click.option('--summary', required=True)
@click.option('--tag', multiple=True)
@click.option('--json', 'as_json', is_flag=True)
def add(symbol, title, summary, tag, as_json):
    \"\"\"Add manual item to review inbox\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager
    manager = create_review_inbox_manager()
    item = manager.add_manual_item(symbol, title, summary, list(tag))

    if as_json:
        click.echo(json.dumps(item.summary(), indent=2))
    else:
        click.echo(f"Added item {item.item_id} for {item.symbol}")

@review.command()
@click.argument('item_id')
@click.option('--build', is_flag=True)
@click.option('--json', 'as_json', is_flag=True)
def checklist(item_id, build, as_json):
    \"\"\"Manage review checklist\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager, create_review_checklist_builder
    manager = create_review_inbox_manager()
    item = manager.get_item(item_id)
    if not item:
        click.echo("Item not found")
        return

    if build:
        builder = create_review_checklist_builder()
        c = builder.build_default_checklist(item, [])
        manager.store.append_checklist(c)
        click.echo("Checklist built")
    else:
        # fetch and display
        click.echo("Checklist not fully implemented for viewing without build flag in this mock.")

@review.command()
@click.argument('item_id')
@click.option('--main', help="Main thesis")
@click.option('--counter', help="Counter thesis")
@click.option('--show', is_flag=True)
@click.option('--json', 'as_json', is_flag=True)
def thesis(item_id, main, counter, show, as_json):
    \"\"\"Manage review thesis\"\"\"
    from bist_signal_bot.app.review_app import create_review_thesis_builder, create_review_store

    if show:
        click.echo("Showing thesis")
    elif main:
        builder = create_review_thesis_builder()
        t = builder.create_thesis(item_id, "SYMBOL", main, counter_thesis=counter or "")
        store = create_review_store()
        store.append_thesis(t)
        click.echo("Thesis added")

@review.command()
@click.argument('item_id')
@click.option('--decision', required=True)
@click.option('--reason', required=True)
@click.option('--confidence', type=float)
def decide(item_id, decision, reason, confidence):
    \"\"\"Make a decision on a review item\"\"\"
    from bist_signal_bot.app.review_app import create_review_decision_manager
    from bist_signal_bot.review.models import ReviewDecisionType
    manager = create_review_decision_manager()

    try:
        dtype = ReviewDecisionType(decision)
        d = manager.decide(item_id, dtype, reason, confidence)
        click.echo(f"Decision recorded: {d.decision_id}")
    except ValueError as e:
        click.echo(f"Error: {e}")

@review.command()
@click.argument('item_id', required=False)
@click.option('--date', help="YYYY-MM-DD")
@click.option('--note')
@click.option('--due', is_flag=True)
@click.option('--clear', is_flag=True)
@click.option('--confirm', is_flag=True)
def followup(item_id, date, note, due, clear, confirm):
    \"\"\"Manage review follow-ups\"\"\"
    from bist_signal_bot.app.review_app import create_review_followup_manager
    from datetime import datetime
    manager = create_review_followup_manager()

    if due:
        items = manager.list_due_followups()
        click.echo(f"Due follow-ups: {len(items)}")
        for i in items:
            click.echo(f"{i.symbol}")
    elif clear and item_id:
        manager.clear_followup(item_id, confirm=confirm)
        click.echo("Follow-up cleared")
    elif date and item_id:
        dt = datetime.strptime(date, "%Y-%m-%d")
        manager.set_followup(item_id, dt, note, confirm=True)
        click.echo("Follow-up set")

@review.command()
@click.option('--symbol')
@click.option('--strategy')
@click.option('--json', 'as_json', is_flag=True)
def journal(symbol, strategy, as_json):
    \"\"\"View decision journal\"\"\"
    from bist_signal_bot.app.review_app import create_decision_journal
    journal = create_decision_journal()
    entries = journal.list_entries(symbol=symbol)

    if as_json:
        data = [e.model_dump(mode="json") for e in entries]
        click.echo(json.dumps(data, indent=2))
    else:
        from bist_signal_bot.review.reporting import format_decision_journal_text
        click.echo(format_decision_journal_text(entries))

@review.command()
@click.option('--json', 'as_json', is_flag=True)
def expire(as_json):
    \"\"\"Expire stale review items\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager
    manager = create_review_inbox_manager()
    expired = manager.expire_stale_items()

    if as_json:
        click.echo(json.dumps([i.item_id for i in expired]))
    else:
        click.echo(f"Expired {len(expired)} items")

@review.command()
@click.option('--json', 'as_json', is_flag=True)
def summary(as_json):
    \"\"\"Show review inbox summary\"\"\"
    from bist_signal_bot.app.review_app import create_review_inbox_manager
    from bist_signal_bot.review.reporting import format_review_inbox_summary
    manager = create_review_inbox_manager()
    s = manager.summary()

    if as_json:
        click.echo(json.dumps(s.model_dump(mode="json"), indent=2))
    else:
        click.echo(format_review_inbox_summary(s))

@review.command()
@click.option('--json', 'as_json', is_flag=True)
def config(as_json):
    \"\"\"Show analyst review config\"\"\"
    from bist_signal_bot.config.settings import Settings
    s = Settings()
    data = {k: v for k, v in s.model_dump().items() if k.startswith("REVIEW_")}
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        for k, v in data.items():
            click.echo(f"{k}: {v}")

"""
    # Find cli definition and add command
    cli_pattern = r'cli\.add_command\((\w+)\)'

    with open(filepath, "w") as f:
        f.write(content + review_command)
        f.write("\ncli.add_command(review)\n")
