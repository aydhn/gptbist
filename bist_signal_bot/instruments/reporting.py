
def instrument_to_dict(record): return record.model_dump()
def lifecycle_event_to_dict(event): return event.model_dump()
def universe_to_dict(universe): return universe.model_dump()

def format_instrument_text(record): return f"{record.symbol} - {record.name} ({record.status.name})"
def format_universe_text(universe): return f"Universe: {universe.name} ({universe.included_count} symbols)"
