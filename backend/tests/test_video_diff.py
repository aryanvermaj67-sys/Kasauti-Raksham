"""changed_ranges: the word diff behind ENDORSEMENT_WORDS_CHANGED (no models needed)."""

from app.comparators.video import changed_ranges


def words(text, t0=0.0):
    return [{"w": w, "start": t0 + i, "end": t0 + i + 0.5} for i, w in enumerate(text.split())]


def test_same_words_report_no_change():
    src = words("the river is wide and slow")
    assert changed_ranges(src, src) == ([], "", "")


def test_quote_keeps_every_word_in_the_range_even_ones_shared_with_the_source():
    src = words("the river is wide and slow near the old town bridge")
    q = words("the cart is full of red and green apples near the old town bridge")
    ranges, said, original = changed_ranges(src, q)
    assert ranges == ["0:01-0:08"]
    assert said == "cart is full of red and green apples"  # "is" and "and" also occur in the source
    assert original == "river is wide and slow"


def test_separate_changes_are_separate_ranges_and_quotes():
    src = words("one two three four five six seven eight nine ten eleven twelve")
    q = words("one six three four five six seven eight nine ten nine twelve")
    ranges, said, original = changed_ranges(src, q)
    assert ranges == ["0:01-0:01", "0:10-0:10"] and said == "six … nine" and original == "two … eleven"
