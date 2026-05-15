with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()

# Add quality dispatch logic
content = content.replace(
    'def dispatch_security(args, ctx) -> int:\n    from bist_signal_bot.cli.commands import handle_security_command\n    handle_security_command(args, ctx.settings)\n    return 0',
    'def dispatch_security(args, ctx) -> int:\n    from bist_signal_bot.cli.commands import handle_security_command\n    handle_security_command(args, ctx.settings)\n    return 0\n\ndef dispatch_quality(args, ctx) -> int:\n    from bist_signal_bot.cli.commands import handle_quality_command\n    handle_quality_command(args, ctx.settings)\n    return 0'
)

# Add it to the commands dict
content = content.replace(
    '"security": dispatch_security,',
    '"security": dispatch_security,\n        "quality": dispatch_quality,'
)

with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(content)
