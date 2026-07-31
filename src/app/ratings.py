from decimal import ROUND_HALF_UP, Decimal

SCORE_STEP = Decimal("0.1")


def _average(scores):
    """Return a one-decimal average for non-empty score lists."""
    if not scores:
        return None
    return (sum(scores) / len(scores)).quantize(SCORE_STEP, rounding=ROUND_HALF_UP)


def effective_score(media, user):
    """Return manual score, or a TV/season average without saving it."""
    from app.models import MediaTypes  # noqa: PLC0415 avoids app.models import cycle

    if media is None:
        return None

    score = getattr(media, "effective_score", media.score)
    if score is not None:
        return Decimal(str(score))

    if not getattr(user, "average_ratings", False):
        return None

    media_type = media.item.media_type
    if media_type == MediaTypes.SEASON.value:
        return _average(
            [
                Decimal(str(episode.score))
                for episode in media.episodes.all()
                if episode.score is not None
            ],
        )

    return (
        _average(
            [
                score
                for season in media.seasons.all()
                if season.item.season_number != 0
                for score in [effective_score(season, user)]
                if score is not None
            ],
        )
        if media_type == MediaTypes.TV.value
        else None
    )


def format_score(score):
    """Return as int if score is 10.0 or 0.0, otherwise show decimal."""
    if score is None:
        return None
    score = Decimal(str(score))
    if score in (Decimal("10.0"), Decimal("0.0")):
        return int(score)
    return score
