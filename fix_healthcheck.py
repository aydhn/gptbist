import re

def fix_healthcheck():
    path = "bist_signal_bot/__main__.py"
    with open(path, "r") as f:
        content = f.read()

    # Add flags to other subcommands
    content = content.replace('p_health.add_argument("--plugins", action="store_true")', 'p_health.add_argument("--plugins", action="store_true")\n    p_health.add_argument("--release-policy", action="store_true")')
    content = content.replace('p_doc.add_argument("--plugins", action="store_true")', 'p_doc.add_argument("--plugins", action="store_true")\n    p_doc.add_argument("--release-policy", action="store_true")')
    content = content.replace('p_qa.add_argument("--include-plugins", action="store_true")', 'p_qa.add_argument("--include-plugins", action="store_true")\n    p_qa.add_argument("--include-release-policy", action="store_true")')
    content = content.replace('p_ops.add_argument("--include-plugins", action="store_true")', 'p_ops.add_argument("--include-plugins", action="store_true")\n    p_ops.add_argument("--include-release-policy", action="store_true")')
    content = content.replace('p_rep.add_argument("--include-plugins", action="store_true")', 'p_rep.add_argument("--include-plugins", action="store_true")\n    p_rep.add_argument("--include-release-policy", action="store_true")')

    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_healthcheck()
