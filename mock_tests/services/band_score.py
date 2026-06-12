"""IELTS Reading/Listening raw score -> band (taxminiy jadval)."""

READING_LISTENING_BANDS = [
    (39, 9.0), (37, 8.5), (35, 8.0), (33, 7.5), (30, 7.0),
    (27, 6.5), (23, 6.0), (19, 5.5), (15, 5.0), (12, 4.5),
    (9, 4.0), (6, 3.5), (4, 3.0), (2, 2.5), (1, 2.0), (0, 1.0),
]


def _lookup_band(scaled_raw):
    scaled = min(40, max(0, int(round(scaled_raw))))
    for min_raw, band in READING_LISTENING_BANDS:
        if scaled >= min_raw:
            return band
    return 1.0


def raw_to_band(correct_count, total_questions=40):
    """To'liq to'g'ri savollar sonidan band (eski API)."""
    if total_questions <= 0:
        return 0.0
    scaled = correct_count * 40 / total_questions
    return _lookup_band(scaled)


def earned_ratio_to_band(earned_points, total_points):
    """Qisman ball bilan band — 40 savolga masshtablab jadvaldan."""
    if total_points <= 0:
        return 0.0
    scaled = float(earned_points) * 40 / float(total_points)
    return _lookup_band(scaled)
