from src.char.Healer import Healer
import time
from src.char.BaseChar import BaseChar, Priority
from decimal import Decimal, ROUND_HALF_UP

class ShoreKeeper(Healer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.liberation_exist_time = 30
        self.liberation_time = 0
        self.liberation_level = 0
        self.has_intro_animation = False
        self.fast_con_combo_count = 0

    def reset_state(self):
        super().reset_state()
        self.liberation_time = 0
        self.liberation_level = 0
        self.has_intro_animation = False
        self.fast_con_combo_count = 0

    def do_get_switch_priority(self, current_char: Healer, has_intro=False, target_low_con=False):
        self.logger.debug(
                f'liberation Remain:{self.liberation_time_left()}s')
        if has_intro and self.liberation_level == 3:
            if 4 <= self.liberation_time_left() <= 8:
                self.logger.info(
                    f'liberation near ending wait for it. Remain:{self.liberation_time_left()}s')
                condition = lambda: (4 <= self.liberation_time_left() <= 8)
                self.handle_pause_switching(current_char, condition)
            if 0 < self.liberation_time_left() < 4:
                self.logger.info(
                    f'switch priority MAX because liberation is about to end. Remain:{self.liberation_time_left()}s')
                self.has_intro_animation = True
                return Priority.MAX + 1
            elif self.liberation_time_left() > 8:
                return Priority.MIN
            else:
                return super().do_get_switch_priority(current_char, has_intro)
        else:
            return super().do_get_switch_priority(current_char, has_intro)
        
    def do_perform(self):
        self.liberation_time_left()
        if self.liberation_level == 0:
            self.fast_con_combo()
            if self.fast_con_combo_count < 2:
                return self.switch_next_char()

        if self.liberation_available(wait_if_cd_ready=0.4):
            if (self.liberation_level == 0 or self.liberation_time_left() < 5) and self.click_liberation():
                self.liberation_level = 1
                self.fast_con_combo_count = 0
                self.liberation_time = time.time()
                self.att_until_con_full()
                
        self.continues_normal_attack(0.1)
        self.switch_next_char()

    def fast_con_combo(self):
        self.fast_con_combo_count += 1
        if self.fast_con_combo_count < 2:
            self.continues_normal_attack(1.1)
            self.sleep(0.3)
            self.continues_right_click(0.1, direction_key='d')
            self.sleep(0.1)
            self.continues_normal_attack(1.1, until_forte_full=False)
        else:
            self.continues_normal_attack(1.3)
            self.sleep(0.1)
        if self.is_forte_full():
            self.heavy_attack(0.6)
            
        if self.fast_con_combo_count > 1:
            self.click_resonance()
            self.click_echo()

    def continues_normal_attack(self, duration, interval=0.1, until_forte_full=True, until_con_full=True):
        start = time.time()
        while time.time() - start < duration:
            if until_forte_full and self.is_forte_full():
                return
            if until_con_full and self.is_con_full():
                return
            self.task.click(interval=interval)

    def att_until_con_full(self):
        start = time.time()
        while not self.is_con_full():
            while not self.is_forte_full() and not self.is_con_full():
                self.check_combat()
                self.click()
                if time.time() - start > 5:
                    self.logger.debug(f'att_until_con_full timeout')
                    break
                self.task.next_frame()
            self.heavy_attack(0.3)
            if time.time() - start > 5:
                self.logger.debug(f'att_until_con_full timeout')
                break
    
    def get_shorekeeper_forte(self):           
        box = self.task.box_of_screen_scaled(3840, 2160, 1628, 1987, 2183, 1993, name='shorekeeper_forte', hcenter=True)
        forte_percent = 0
        forte_percent = self.task.calculate_color_percentage(shorekeeper_forte_color, box)
        forte_percent = Decimal(str(forte_percent)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.logger.debug(f'forte_percent {forte_percent}')
        return forte_percent
    
    def handle_intro_animation(self):
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
                    self.add_freeze_duration(animation_start, duration)
                    self.liberation_level = 0
                    self.has_intro_animation = False
                    break
                elif time.time() - start > 1:
                    self.logger.info(f'Discernment fail')
                    break
                else:
                    self.task.send_key(self.index + 1)
                    self.task.next_frame()
            else:
                if animation_start == 0:
                    self.logger.info(f'Discernment start animation')
                    animation_start = time.time()
            self.task.next_frame()

    def liberation_time_left(self):
        if self.liberation_level != 0:
            remain = self.liberation_exist_time - self.total_time_elapsed_accounting_for_freeze(self.liberation_time)
            if remain < 0:
                self.liberation_level = 0
        else:
            remain = 0
        return remain

    def add_liberation_level(self):
        if 0 < self.liberation_level < 3:
            self.liberation_level += 1

shorekeeper_forte_color = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (121, 141)   # Blue range
}