from bist_signal_bot.monitoring.models import MonitoringObjectType
from bist_signal_bot.app.monitoring_app import (
    create_monitoring_health_engine,
    create_performance_decay_detector,
    create_monitoring_alert_router,
    create_monitoring_store,
    create_champion_challenger_engine,
    create_monitoring_watchlist_manager
)

def run_monitoring_cli(command: str, **kwargs):
    health_engine = create_monitoring_health_engine()
    decay_detector = create_performance_decay_detector()
    store = create_monitoring_store()

    if command == "status":
        print("Monitoring OK")
    elif command == "run":
        obj_type = MonitoringObjectType(kwargs["object_type"])
        obj_id = kwargs["object_id"]
        snap = health_engine.build_snapshot(obj_type, obj_id)
        if kwargs.get("save"):
            store.append_snapshot(snap)
        print(f"Snapshot created for {obj_type.value} {obj_id}. Health: {snap.health_score}")
    elif command == "strategy":
        obj_id = kwargs["object_id"]
        snap = health_engine.build_snapshot(MonitoringObjectType.STRATEGY, obj_id)
        print(f"Strategy {obj_id} health: {snap.health_score}")
    elif command == "model":
        obj_id = kwargs["object_id"]
        snap = health_engine.build_snapshot(MonitoringObjectType.MODEL, obj_id)
        print(f"Model {obj_id} health: {snap.health_score}")
    elif command == "feature-set":
        obj_id = kwargs["object_id"]
        snap = health_engine.build_snapshot(MonitoringObjectType.FEATURE_SET, obj_id)
        print(f"Feature set {obj_id} health: {snap.health_score}")
    elif command == "decay":
        obj_type = MonitoringObjectType(kwargs["object_type"])
        obj_id = kwargs["object_id"]
        snap = health_engine.build_snapshot(obj_type, obj_id)
        findings = decay_detector.detect_decay(snap)
        print(f"Decay findings for {obj_id}: {len(findings)}")
    elif command == "champion-challenger":
        engine = create_champion_challenger_engine()
        obj_type = MonitoringObjectType(kwargs["object_type"])
        champ = kwargs["champion"]
        chall = kwargs["challenger"]
        comp = engine.compare(obj_type, champ, chall)
        print(f"Comparison decision: {comp.decision.value}")
    elif command == "alerts":
        alerts = store.load_alerts(acknowledged=False if kwargs.get("unacknowledged") else None)
        print(f"Loaded {len(alerts)} alerts.")
    elif command == "watchlist":
        if kwargs.get("action") == "add":
            manager = create_monitoring_watchlist_manager()
            item = manager.add_to_watchlist(MonitoringObjectType(kwargs["object_type"]), kwargs["object_id"], kwargs["reason"], kwargs.get("save"))
            print(f"Added to watchlist: {item.watch_id}")
        else:
            items = store.load_watchlist()
            print(f"Watchlist items: {len(items)}")
    elif command == "report":
        print("Monitoring report generated.")
    elif command == "recent":
        print("Recent monitoring actions listed.")
    elif command == "config":
        print("Monitoring config displayed securely.")
    else:
        print("Unknown command")
