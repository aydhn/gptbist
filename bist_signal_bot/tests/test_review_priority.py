from bist_signal_bot.review_workflow.priority import ReviewPriorityEngine
from bist_signal_bot.review_workflow.models import ReviewCasePriority

def test_priority_from_conflicts_critical():
    engine = ReviewPriorityEngine()
    assert engine.priority_from_conflicts(["CRITICAL"]) == ReviewCasePriority.CRITICAL

def test_priority_from_gaps_high():
    engine = ReviewPriorityEngine()
    assert engine.priority_from_gaps(["g1", "g2", "g3", "g4"]) == ReviewCasePriority.HIGH

def test_requires_signoff():
    engine = ReviewPriorityEngine()
    assert engine.requires_signoff(ReviewCasePriority.CRITICAL) == True
    assert engine.requires_signoff(ReviewCasePriority.HIGH) == False
    assert engine.requires_signoff(ReviewCasePriority.LOW, conflicts=["CRITICAL"]) == True
