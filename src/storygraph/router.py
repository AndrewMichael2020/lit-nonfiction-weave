from .state import StoryState
from .agents import planner, draft, fact, revision, research
from .validators import total_words, within_band, audit_beats


class Pipeline:
    def __init__(self, seed: int = 137):
        self.state = StoryState(seed=seed)

    def run_minimal(self, premise: str, venue: str, models: dict = None, context: dict = None):
        s = self.state
        s.premise, s.venue = premise, venue
        models = models or {}
        context = context or {}
        s = planner.run(s, model=models.get("planner"), context=context)
        s = draft.run(s, model=models.get("draft"), context=context)
        s = fact.run(s, model=models.get("fact"), context=context)
        s = revision.run(s, model=models.get("revision"))
        # metrics
        drafts = {k: v.text for k, v in s.drafts.items()}
        targets = {b.id: b.target_words for b in s.outline.beats}
        s.metrics["beat_within"] = audit_beats(drafts, targets, 0.15)
        s.metrics["word_count_v2"] = total_words(s.draft_v2_concat)
        s.metrics["within_band"] = within_band(
            s.metrics["word_count_v2"], s.word_target_low, s.word_target_high
        )
        self.state = s
        return s
