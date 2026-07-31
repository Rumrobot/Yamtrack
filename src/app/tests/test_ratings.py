from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from app.models import TV, Episode, Item, MediaTypes, Season, Sources, Status
from app.ratings import effective_score, format_score


class EffectiveScoreTests(TestCase):
    """Test computed ratings for TV and seasons."""

    def setUp(self):
        """Create a TV show with one season and two rated episodes."""
        self.user = get_user_model().objects.create_user(
            username="ratings",
            average_ratings=True,
        )
        tv_item = Item.objects.create(
            media_id="show1",
            source=Sources.TMDB.value,
            media_type=MediaTypes.TV.value,
            title="Show",
            image="none.jpg",
        )
        season_item = Item.objects.create(
            media_id="show1",
            source=Sources.TMDB.value,
            media_type=MediaTypes.SEASON.value,
            title="Show",
            image="none.jpg",
            season_number=1,
        )
        self.tv = TV.objects.create(
            user=self.user,
            item=tv_item,
            status=Status.PLANNING.value,
        )
        self.season = Season.objects.create(
            user=self.user,
            item=season_item,
            related_tv=self.tv,
            status=Status.PLANNING.value,
        )
        Episode.objects.bulk_create(
            [
                Episode(
                    item=Item.objects.create(
                        media_id="show1",
                        source=Sources.TMDB.value,
                        media_type=MediaTypes.EPISODE.value,
                        title="Show",
                        image="none.jpg",
                        season_number=1,
                        episode_number=1,
                    ),
                    related_season=self.season,
                    score=Decimal("7.0"),
                ),
                Episode(
                    item=Item.objects.create(
                        media_id="show1",
                        source=Sources.TMDB.value,
                        media_type=MediaTypes.EPISODE.value,
                        title="Show",
                        image="none.jpg",
                        season_number=1,
                        episode_number=2,
                    ),
                    related_season=self.season,
                    score=Decimal("8.0"),
                ),
            ],
        )

    def test_effective_score_averages_episode_scores_for_unrated_season(self):
        """An unrated season uses its episode rating average."""
        self.assertEqual(effective_score(self.season, self.user), Decimal("7.5"))

    def test_effective_score_averages_effective_season_scores_for_unrated_tv(self):
        """An unrated TV show uses its season rating average."""
        self.assertEqual(effective_score(self.tv, self.user), Decimal("7.5"))

    def test_effective_score_uses_manual_score_before_average(self):
        """Manual ratings override computed averages."""
        self.season.score = Decimal("9.0")

        self.assertEqual(effective_score(self.season, self.user), Decimal("9.0"))

    def test_effective_score_returns_none_when_setting_is_disabled(self):
        """Computed ratings are opt-in."""
        self.user.average_ratings = False

        self.assertIsNone(effective_score(self.season, self.user))



class FormatScoreTests(SimpleTestCase):
    """Test score display formatting."""

    def test_hides_trailing_decimal_for_extremes(self):
        """Whole endpoint scores display without decimal noise."""
        self.assertEqual(format_score(Decimal("10.0")), 10)
        self.assertEqual(format_score(Decimal("0.0")), 0)
        self.assertEqual(format_score(Decimal("7.5")), Decimal("7.5"))
