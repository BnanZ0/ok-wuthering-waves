import time

from ok import TriggerTask, Logger
from src.char.CharFactory import char_names
from src.scene.WWScene import WWScene
from src.task.BaseCombatTask import BaseCombatTask, NotInCombatException, CharDeadException

logger = Logger.get_logger(__name__)


class AutoCombatTask(BaseCombatTask, TriggerTask):
    owns_switch_healer_config = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_config = {'_enabled': True}
        self.trigger_interval = 0.1
        self.name = "⚔️ Auto Combat"
        self.description = "Enable auto combat in Abyss, Game World etc"
        self.last_is_click = False
        self.default_config.update({
            'Auto Target': True,
            'Use Liberation': True,
            'Check Levitator': True,
            'Switch to Healer before and after Combat': True,
            'Single Character': False,
        })
        self.config_description = {
            'Auto Target': 'Turn off to enable auto combat only when manually target enemy using middle click',
            'Use Liberation': 'Do not use Liberation in Open World to Save Time',
            'Check Levitator': 'Toggle the levitator and verify if the character is floating',
            'Switch to Healer before and after Combat': 'Better Chance to Keep Character Alive',
            'Single Character': 'Storyline use only. Character specific bugs will not be fixed',
            'Force Two Characters': 'Force only use two characters'
        }
        self.op_index = 0
        self.origin_func = {}
        self.char_features_warmed_up = False

    def warm_up_char_features(self):
        if self.char_features_warmed_up:
            return
        try:
            for char_name in char_names:
                self.get_feature_by_name(char_name)
        except Exception as e:
            logger.warning(f'warm_up_char_features failed: {e}')
            return
        self.char_features_warmed_up = True
        logger.info(f'warm_up_char_features loaded {len(char_names)} character templates')

    def run(self):
        self.toggle_single_character_mode()
        self.warm_up_char_features()
        ret = False
        if not self.scene.in_team(self.in_team_and_world):
            return ret
        self.use_liberation = self.config.get('Use Liberation')
        if not self.use_liberation and not self.in_world():  # 仅大世界生效
            self.use_liberation = True
        
        if hasattr(self, 'test') and callable(getattr(self, 'test')):
            self.test()
            return ret
        if False:
            self.load_chars()
            char = self.get_current_char()
            if hasattr(char, 'test') and callable(getattr(char, 'test')):
                import types
                original_in_combat = self.in_combat
                self.in_combat = types.MethodType(lambda _self: True, self)
                char.test()
                self.in_combat = original_in_combat
        
        combat_start = time.time()
        switched_to_healer = False
        while self.in_combat():
            ret = True
            try:
                if not switched_to_healer:
                    self.switch_healer()
                    switched_to_healer = True
                self.get_current_char().perform()
            except CharDeadException:
                self.log_error(f'Characters dead', notify=True)
                break
            except NotInCombatException as e:
                logger.info(f'auto_combat_task_out_of_combat {int(time.time() - combat_start)} {e}')
                break
        if ret:
            self.combat_end()
            self.switch_healer()
        return ret

    def realm_perform(self):
        if not self.last_is_click:
            if self.op_index % 10 == 0:
                self.send_key_and_wait_animation('4', self.in_illusive_realm, enter_animation_wait=0.2)
            else:
                self.click()
        else:
            if self.available('liberation'):
                self.send_key_and_wait_animation(self.get_liberation_key(), self.in_illusive_realm)
            elif self.available('echo'):
                self.send_key(self.get_echo_key())
            elif self.available('resonance'):
                self.send_key(self.get_resonance_key())
            elif self.is_con_full() and self.in_team()[0]:
                self.send_key_and_wait_animation('2', self.in_illusive_realm)
        self.last_is_click = not self.last_is_click
        self.op_index += 1
        self.sleep(0.02)

    def toggle_single_character_mode(self):
        close_single_mode = False
        single_mode = self.config.get('Single Character')
        if single_mode:
            if self.origin_func and self.origin_func["in_team"]()[0]:
                close_single_mode = True
            if not self.origin_func:
                self.log_info("Single Character Mode Enabled")
                self.origin_func["in_team"] = self.in_team
                self.origin_func["load_chars"] = self.load_chars
                self.origin_func["switch_next_char"] = self.switch_next_char
                self.in_team = self.single_character_in_team
                self.load_chars = self.load_single_char
                self.switch_next_char = self.single_character_switch_next

        if not single_mode and self.origin_func or close_single_mode:
            self.log_info("Single Character Mode Disabled")
            self.chars = [None, None, None]
            self.in_team = self.origin_func["in_team"]
            self.load_chars = self.origin_func["load_chars"]
            self.switch_next_char = self.origin_func["switch_next_char"]
            self.origin_func.clear()

    def single_character_in_team(self):
        box = self.box_of_screen(0.7867, 0.9250, 0.9566, 0.9542)
        if self.find_best_match_in_box(to_find=["r", "e"], box=box, threshold=0.75):
            self._logged_in = True
            return True, 0, 1
        else:
            return False, -1, 1

    def single_character_switch_next(self, *args, **kwargs):
        self.click(interval=0.1)
        self.send_key('f', after_sleep=0.1)


from ok import run_task
from config import config

if __name__ == "__main__":
    run_task(config, task=AutoCombatTask, debug=True)
