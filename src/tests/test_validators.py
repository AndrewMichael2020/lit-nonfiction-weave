from storygraph.validators import beat_within_tolerance


def test_beat_tol():
    assert beat_within_tolerance(575, 500, 0.15) is True
    assert beat_within_tolerance(751, 650, 0.15) is True
    assert beat_within_tolerance(900, 600, 0.15) is False
