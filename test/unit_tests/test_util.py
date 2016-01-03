import mock

from slackbot_workout import util

class TestUtil(object):
    @mock.patch('slackbot_workout.util.time')
    def test_sleep_seconds(self, mock_time):
        util.sleep(seconds=30)
        mock_time.sleep.assert_called_with(30)

    @mock.patch('slackbot_workout.util.time')
    def test_sleep_minutes_seconds(self, mock_time):
        util.sleep(minutes=3, seconds=30)
        mock_time.sleep.assert_called_with(210)
