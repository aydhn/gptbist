import sys
from bist_signal_bot.cli.research_orchestrator_cli import main as ro_main

def handle_orchestrator(args):
    return ro_main(args)

# Hook into existing __main__.py logic manually or provide instruction
