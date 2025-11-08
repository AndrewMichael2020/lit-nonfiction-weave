from collections import Counter
import re


def sentence_lengths(text: str):
    sents = re.split(r"(?<=[.!?])\s+", text.strip()) if text.strip() else []
    return [len(s.split()) for s in sents if s]
