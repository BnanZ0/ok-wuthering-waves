from src.char.Healer import Healer
import time
from enum import Enum
from src.char.BaseChar import BaseChar, Priority
from decimal import Decimal, ROUND_HALF_UP

class Char_Action(Enum):
    FORTE_FULL = 1
    CON_FULL = 2
    DONE = 3
    HEAVY_ATT = 4
class ShoreKeeper(Healer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.liberation_exist_time = 30
        self.liberation_time = 0
        self.liberation_level = 0
        self.has_intro_animation = False
        self.fast_con_combo_count = 0

        self.released_outro_this_liberation = False

    def reset_state(self):
        super().reset_state()
        self.liberation_time = 0
        self.liberation_level = 0
        self.has_intro_animation = False
        self.fast_con_combo_count = 0

    def do_get_switch_priority(self, current_char: Healer, has_intro=False, target_low_con=False):
        self.logger.debug(f'liberation Remain:{self.liberation_time_left()}s')
        if has_intro and self.liberation_level == 3:
            if 0 < self.liberation_time_left() < 4:
                self.logger.info(f'switch priority MAX because liberation is about to end. Remain:{self.liberation_time_left()}s')
                self.has_intro_animation = True
                return Priority.MAX - 1
            elif self.liberation_time_left() > 8:
                return Priority.MIN
            """ elif 4 <= self.liberation_time_left() <= 8:
                return Priority.MAX - 1 """
        elif self.liberation_level < 3 and not self.released_outro_this_liberation:
            return Priority.SKILL_AVAILABLE + 100
        return super().do_get_switch_priority(current_char, has_intro)
        
    def should_pause_switch(self):
        now = time.time()
        if not hasattr(self, "last_print_time"):
            self.last_print_time = 0
        if self.has_intro and self.liberation_level == 3:
            time_left = self.liberation_time_left()
            if 4 <= time_left <= 8:
                if now - self.last_print_time >= 3:
                    self.last_print_time = now
                    self.logger.info(f'liberation near ending wait for it. Remain:{self.liberation_time_left()}s')
                return True
            if 0 < time_left < 4:
                self.logger.info(f'liberation is about to end. Remain:{self.liberation_time_left()}s')
                self.has_intro_animation = True
        return False
        
    def do_perform(self):
        self.liberation_time_left()
        cast_liberation = False
        if self.should_cast_liberation():
            if self.resonance_available():
                target_con = 0.5
            else:
                target_con = 0.8
            if self.get_current_con() < target_con:
                result = self.fast_con_combo()
                self.fast_con_combo_count += 1
                if self.get_current_con() > target_con:
                    cast_liberation = True
                if not cast_liberation and self.fast_con_combo_count > 1:
                    if result == Char_Action.HEAVY_ATT:
                        self.sleep(0.2)
                        self.continues_right_click(0.1)
                    while self.get_current_con() < target_con:
                        self.check_combat()
                        self.click()
                        if self.is_forte_full():
                            self.heavy_attack(0.6)
                            self.sleep(0.2)
                            self.continues_right_click(0.1)
                        self.task.next_frame()
                    cast_liberation = True
                elif not cast_liberation:
                    return self.switch_next_char()
            else:
                cast_liberation = True

        if cast_liberation:
            if self.resonance_available():
                self.click_resonance()
            if self.click_liberation():
                self.liberation_level = 1
                self.liberation_time = time.time()
                self.released_outro_this_liberation = False
                self.fast_con_combo_count = 0
                self.att_until_con_full()

        if self.is_forte_full():
            self.heavy_attack(0.6)
        self.continues_normal_attack(0.1)
        self.switch_next_char()

    def fast_con_combo(self):
        result = self.continues_normal_attack(1.1)
        if result != Char_Action.CON_FULL:
            if result != Char_Action.FORTE_FULL:
                self.sleep(0.3)
                self.continues_right_click(0.1, direction_key='d')
                self.sleep(0.1)
                result = self.continues_normal_attack(1.4)
            if result != Char_Action.CON_FULL and (result == Char_Action.FORTE_FULL or self.is_forte_full()):
                self.heavy_attack(0.6)
                return Char_Action.HEAVY_ATT
        return Char_Action.DONE

    def should_cast_liberation(self):
        return self.liberation_level == 0 or self.liberation_time_left() < 5
    #未使用
    def fast_con_combo2(self):
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
                return Char_Action.FORTE_FULL
            if until_con_full and self.is_con_full():
                return Char_Action.CON_FULL
            self.task.click(interval=interval)
        return Char_Action.DONE
        
    #未使用
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
    #未使用
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
        self.task.in_liberation = True
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
                    self.sleep(0.4)
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
        self.task.in_liberation = False

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

    def switch_next_char(self, *args):
        if self.is_con_full():
            self.released_outro_this_liberation = True
        return super().switch_next_char(*args)
    
shorekeeper_forte_color = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (121, 141)   # Blue range
}