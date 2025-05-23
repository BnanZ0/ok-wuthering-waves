from ok import TriggerTask, Logger
from src.task.SkipBaseTask import SkipBaseTask

logger = Logger.get_logger(__name__)


class AutoDialogTask(TriggerTask, SkipBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_config = {'_enabled': True}
        self.skip = None
        self.trigger_interval = 0.5
        self.name = "Skip Dialog during Quests"

    def run(self):
        if self.scene.in_team(self.in_team_and_world):
            return
        return self.check_skip()
