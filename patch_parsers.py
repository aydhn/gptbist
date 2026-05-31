
import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

patch = '''
    # Monitoring Subparser
    monitoring_parser = subparsers.add_parser('monitoring', help='Research monitoring and champion/challenger')
    monitoring_sub = monitoring_parser.add_subparsers(dest='monitoring_cmd', help='Monitoring commands')

    m_status = monitoring_sub.add_parser('status')
    m_status.add_argument('--json', action='store_true')

    m_run = monitoring_sub.add_parser('run')
    m_run.add_argument('--object-type')
    m_run.add_argument('--object-id')
    m_run.add_argument('--save', action='store_true')
    m_run.add_argument('--json', action='store_true')

    m_strategy = monitoring_sub.add_parser('strategy')
    m_strategy.add_argument('strategy_id')
    m_strategy.add_argument('--json', action='store_true')

    m_model = monitoring_sub.add_parser('model')
    m_model.add_argument('model_id')
    m_model.add_argument('--json', action='store_true')

    m_feature_set = monitoring_sub.add_parser('feature-set')
    m_feature_set.add_argument('feature_set_id')
    m_feature_set.add_argument('--json', action='store_true')

    m_decay = monitoring_sub.add_parser('decay')
    m_decay.add_argument('--object-type')
    m_decay.add_argument('--object-id')
    m_decay.add_argument('--json', action='store_true')

    m_cc = monitoring_sub.add_parser('champion-challenger')
    m_cc.add_argument('--object-type')
    m_cc.add_argument('--champion')
    m_cc.add_argument('--challenger')
    m_cc.add_argument('--json', action='store_true')

    m_alerts = monitoring_sub.add_parser('alerts')
    m_alerts.add_argument('--unacknowledged', action='store_true')
    m_alerts.add_argument('--ack')
    m_alerts.add_argument('--note')
    m_alerts.add_argument('--json', action='store_true')

    m_watch = monitoring_sub.add_parser('watchlist')
    m_watch.add_argument('--json', action='store_true')
    m_watch_sub = m_watch.add_subparsers(dest='watch_cmd')
    m_watch_add = m_watch_sub.add_parser('add')
    m_watch_add.add_argument('--object-type')
    m_watch_add.add_argument('--object-id')
    m_watch_add.add_argument('--reason')
    m_watch_add.add_argument('--save', action='store_true')
    m_watch_add.add_argument('--json', action='store_true')

    m_report = monitoring_sub.add_parser('report')
    m_report.add_argument('--latest', action='store_true')
    m_report.add_argument('--json', action='store_true')

    m_recent = monitoring_sub.add_parser('recent')
    m_recent.add_argument('--limit', type=int, default=10)
    m_recent.add_argument('--json', action='store_true')

    m_config = monitoring_sub.add_parser('config')
    m_config.add_argument('--json', action='store_true')
'''
# Find the place where subparsers are defined and append
content = re.sub(r"(subparsers = parser.add_subparsers\(dest='command', help='Available commands'\))", r"\1" + patch, content)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
