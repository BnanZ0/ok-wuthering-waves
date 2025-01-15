from src.char.Healer import Healer
import time
from src.char.BaseChar import BaseChar, Priority

class ShoreKeeper(Healer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.liberation_exist_time = 30
        self.liberation_time = 0
        self.liberation_remain = 0
        self.liberation_level = 0
        self.discernment = False
        self.wait_for_discernment = False

    def reset_state(self):
        super().reset_state()
        self.liberation_time = 0
        self.liberation_remain = 0
        self.liberation_level = 0
        self.discernment = False
        self.wait_for_discernment = False

    def do_get_switch_priority(self, current_char: Healer, has_intro=False, target_low_con=False):
        self.update_liberation_remain()
        self.logger.info(
                f'liberation Remain:{self.liberation_remain}s')
        if has_intro and 0 < self.liberation_remain < 5 and self.liberation_level == 3:
            self.logger.info(
                f'switch priority MAX because liberation is about to end. Remain:{self.liberation_remain}s')
            self.wait_for_discernment = False
            self.discernment = True
            return Priority.MAX + 1
        elif has_intro and 0 < self.liberation_remain < 15 and self.liberation_level == 3:
            self.logger.info(
                f'liberation near ending wait for it. Remain:{self.liberation_remain}s')
            self.wait_for_discernment = True
            return Priority.SKILL_AVAILABLE
        else:
            return super().do_get_switch_priority(current_char, has_intro)
        
    def do_perform(self):
        if self.has_intro:
            self.logger.debug('ShoreKeeper wait intro animation')
            # self.task.wait_in_team_and_world(time_out=4, raise_if_not_found=False)
            # self.check_combat()

        if self.liberation_available(wait_if_cd_ready=0.4):
            if self.liberation_level != 0:
                self.update_liberation_remain()
            if (self.liberation_level == 0 or self.liberation_remain < 5) and self.click_liberation(wait_if_cd_ready=0.4):
                self.liberation_level = 1
                self.liberation_time = time.time()

        self.click_resonance(send_click=False)
        self.click_echo()
        if self.is_forte_full():
            self.heavy_attack()
        self.switch_next_char()

    def handle_discernment(self):
        start = time.time()
        animation_start = 0
        duration = 0
        while True:
            if time.time() - start > 6:
                self.logger.info(f'Handle discernment too long')
                break
            if self.task.in_team()[0]:
                if animation_start != 0:
                    self.logger.info(f'Discernment done')
                    duration = time.time() - animation_start
                    self.discernment = False
                    self.liberation_level = 0
                    break
                elif time.time() - start > 1:
                    self.logger.info(f'Discernment fail')
                    break
            else:
                if animation_start == 0:
                    self.logger.info(f'Discernment start animation')
                    animation_start = time.time()
            self.task.next_frame()
        if not self.discernment:
            self.add_freeze_duration(animation_start, duration)

    def update_liberation_remain(self):
        self.liberation_remain = self.liberation_exist_time - self.time_elapsed_accounting_for_freeze(self.liberation_time)

    def add_liberation_level(self):
        if 0 < self.liberation_level < 3:
            self.liberation_level += 1