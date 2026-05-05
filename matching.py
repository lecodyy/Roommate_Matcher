# matching.py

def year_similarity(year1, year2):
    if not year1 or not year2:
        return 0
    diff = abs(year1 - year2)
    return max(0, 1 - (diff / 4))  # max diff of 4 (freshman vs senior)


def calculate_compatibility(user, other):
    score = 0
    max_score = 0

    # Budget (25%)
    if user.budget and other.budget:
        budget_diff = abs(user.budget - other.budget)
        budget_score = max(0, 100 - budget_diff)
        score += budget_score * 0.25
        max_score += 100 * 0.25

    # Noise level (20%)
    if user.noise_level and other.noise_level:
        diff = abs(user.noise_level - other.noise_level)
        score += max(0, 100 - diff) * 0.20
        max_score += 100 * 0.20

    # Cleanliness (15%)
    if user.cleanliness and other.cleanliness:
        diff = abs(user.cleanliness - other.cleanliness)
        score += max(0, 100 - diff) * 0.15
        max_score += 100 * 0.15

    # Sleep schedule (15%)
    sleep_order = {'early': 0, 'normal': 1, 'night': 2}
    if user.sleep_schedule and other.sleep_schedule:
        diff = abs(sleep_order[user.sleep_schedule] - sleep_order[other.sleep_schedule])
        score += max(0, 100 - (diff * 50)) * 0.15
        max_score += 100 * 0.15

    # Class year (10%)
    if user.year and other.year:
        score += year_similarity(user.year, other.year) * 100 * 0.10
        max_score += 100 * 0.10

    # Smoking (10%)
    if user.smoking is not None and other.smoking is not None:
        score += 100 * 0.10 if user.smoking == other.smoking else 0
        max_score += 100 * 0.10

    # Drinking (5%)
    if user.drinking is not None and other.drinking is not None:
        score += 100 * 0.05 if user.drinking == other.drinking else 0
        max_score += 100 * 0.05

    if max_score == 0:
        return 0
    return round((score / max_score) * 100, 1)