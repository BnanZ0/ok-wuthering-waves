import time
from decimal import Decimal, ROUND_HALF_UP

from src.char.BaseChar import BaseChar, Priority, forte_white_color
from src.combat.CombatCheck import aim_color

class Zani(BaseChar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intro_motion_freeze_duration = 1.4
        self.liberation_time = 0
        self.in_liberation = False
        self.blazes = -1
        self.blazes_threshold = -1
        self.char_phoebe = None
        self.crisis_time = -1
        self.nightfall_time = -1
        self.normal_resonance_time = -1
        self.state = 0
        
    def reset_state(self):
        self.char_phoebe = None
        self.blazes_threshold = -1
        self.state = 0
        super().reset_state()

    def count_resonance_priority(self):
        return 5
        
    def do_perform(self): 
        if self.blazes_threshold == -1:
            self.decide_teammate()
        if self.has_intro:
            self.continues_normal_attack(1.3)
        self.check_liber()
        if self.echo_available():
            self.click_echo()

        if self.in_liberation:
            self.logger.info(f'in liberation')
            if self.should_end_liberation():
                if self.click_liber2():
                    self.state = 2
                    return
            else:
                self.nightfall_combo()
            return self.switch_next_char()

        cast_liberation = False
        if self.crisis_time > 0:
            self.wait_for_crisis_protocol_end()
            if self.crisis_time_left() > - 1 and self.liberation_available():
                cast_liberation = True
            self.crisis_time = - 1

        if not cast_liberation and (self.is_prepared() or self.is_phoebe_complete()):
            self.logger.info(f'ready')
            if not self.has_cd('liberation'):
                self.logger.info(f'liberation no cd')
                self.crisis_response_protocol_combo()
                if self.liberation_available():
                    cast_liberation = True
                    if self.blazes != 1:
                        self.wait_for_crisis_protocol_end()
                    self.crisis_time = - 1
                else:
                    return self.switch_next_char()
            else:
                if self.standard_defense_protocol_combo():
                    if not self.wait_until_forte_full(1.2):
                        self.click()
                else:
                    if self.is_forte_full():
                        self.crisis_response_protocol_combo()
                    else:
                        self.continues_normal_attack(0.1)
                return self.switch_next_char()

        if cast_liberation:
            if self.click_liberation():
                self.state = 1
                self.in_liberation = True
                self.liberation_time = time.time()
                self.check_liber()
                self.continues_right_click(0.1)
                self.continues_normal_attack(0.1)
                self.nightfall_combo(cancel_last_smash = True)
                self.sleep(0.1)
                self.nightfall_combo()
                return self.switch_next_char()
        
        if not self.is_phoebe_complete():
            self.logger.info(f'last operation')
            if (self.current_liberation() == 0 
                and not self.has_cd('liberation') 
            ):
                self.logger.info(f'gain forte')
                if self.standard_defense_protocol_combo():
                    if not self.wait_until_forte_full(1.2):
                        self.click()
                if self.is_forte_full():
                    self.crisis_response_protocol_combo()
            else:
                self.logger.info(f'do something')
                if not self.standard_defense_protocol_combo():
                    self.continues_normal_attack(0.1)
        self.switch_next_char()          

    def click_liber2(self, switch_char=True):
        if self.liberation_available():   
            start = time.time()
            self.check_liber()
            if self.in_liberation:
                self.send_liberation_key()
                self.task.in_liberation = True
                if switch_char:
                    self.switch_next_char()
                if time.time() - start > 2:
                    self.add_freeze_duration(start, time.time()-start)
                    self.logger.debug(f'Zani click liber2 in {time.time()-start}')
                    self.in_liberation = False
                    self.blazes = -1
                    self.liberation_time = -1
                self.task.in_liberation = False
                return True
        return False
        
    def should_end_liberation(self, check_forte=True):
        result = self.total_time_elapsed_accounting_for_freeze(self.liberation_time)
        self.logger.debug(f'liberation_lasted: {result}')
        if self.liberation_time_left() < 1.7:
            self.logger.info(f'liberation is about to end, perform liberation2')
            return True
        if self.is_nightfall_ready():
            return False
        if check_forte:
            self.wait_resonance_not_gray()
            if not self.is_forte_full():
                self.logger.info(f'Cannot perform another nightfall, perform liberation2')
                return True
        return False
    
    def liberation_time_left(self):
        if not self.in_liberation or self.liberation_time <= 0:
            return 0
        result = 20 - self.total_time_elapsed_accounting_for_freeze(self.liberation_time)
        self.logger.debug(f'liberation_lasted: {result}')
        return result
    
    def nightfall_combo(self, cancel_last_smash = False):
        self.logger.info(f'perform nightfall_combo')
        start = time.time()
        if not self.is_nightfall_ready():
            while not self.is_nightfall_ready() or time.time() - start < 1.6:
                self.click()
                if time.time() - start > 3.5 or not self.in_liberation:
                    return
                if self.should_end_liberation(check_forte=False) and self.click_liber2():
                    return
                self.check_combat()
                self.task.next_frame()
        self.continues_normal_attack(0.5)
        if cancel_last_smash:
            self.logger.info(f'cancel nightfall last smash')
            while self.is_nightfall_ready(threshold = 0.035):
                self.click()
                self.task.next_frame()
            self.sleep(0.1)
            self.continues_right_click(0.1)
        else:
            self.nightfall_time = time.time()

    def is_nightfall_ready(self, threshold = 0.05):
        box = self.task.box_of_screen_scaled(3840, 2160, 2680, 1845, 2862, 2025, name='zani_attack', hcenter=True)
        light_percent = self.task.calculate_color_percentage(zani_light_color, box)
        self.logger.debug(f'nightfall_percent {light_percent}')
        if light_percent > threshold:
            return True
        return False
    
    def nightfall_time_left(self):
        if self.nightfall_time <= 0:
            return 0
        result = 2.1 - self.total_time_elapsed_accounting_for_freeze(self.nightfall_time, intro_freeze=True)
        if self.nightfall_time <= 0:
            self.nightfall_time = -1
            return 0
        self.logger.debug(f'nightfall_time_left: {result}')
        return result
    
    def standard_defense_protocol_combo(self):
        self.logger.debug(f'perform standard_defense_protocol')
        if self.is_forte_full():
            return False
        if self.resonance_available():
            self.update_res_cd()
            self.send_resonance_key()
            self.normal_resonance_time = time.time()
            self.sleep(0.1)
            self.continues_normal_attack(0.1)
            return True
        return False
    
    def crisis_response_protocol_combo(self):
        self.logger.info(f'perform crisis_response_protocol')
        if not self.is_forte_full():
            for _ in range(2):
                if not self.standard_defense_protocol_combo():
                    self.heavy_attack(duration=0.6)
                    self.sleep(0.55)
                    self.continues_normal_attack(0.1)
                if self.wait_until_forte_full(1.2):
                    break
                self.click()
                if self.wait_until_forte_full(1.9):
                    break
                else:
                    self.continues_right_click(0.1)
                    self.sleep(0.1)
                if self.is_forte_full():
                    break
            else:
                while not self.is_forte_full():
                    self.click()
                    self.check_combat()
                    self.task.next_frame()
        while True:
            self.check_combat()
            self.send_resonance_key()
            if not self.is_forte_full():
                break
            self.task.next_frame()
        self.crisis_time = time.time()

    def wait_until_forte_full(self, timeout=1):
        start = time.time()
        while time.time() - start < timeout:
            if self.is_forte_full():
                return True
            self.check_combat()
            self.task.next_frame()
        return False
    
    def is_forte_full(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2284, 1992, 2311, 2019, name='forte_full', hcenter=True)
        n = 2
        for i in range(n):
            white_percent = self.task.calculate_color_percentage(forte_white_color, box)
            self.logger.debug(f'forte_color_percent {white_percent}')
            if white_percent < 0.12:
                break
            if i < n - 1:
                self.sleep(0.1)
        return white_percent > 0.12

    def crisis_time_left(self):
        if self.crisis_time <= 0:
            return 0
        result = 1.8 - self.total_time_elapsed_accounting_for_freeze(self.crisis_time)
        self.logger.debug(f'crisis_time_left: {result}')
        return result
    
    def wait_for_crisis_protocol_end(self):
        if self.normal_resonance_time > 0 and self.total_time_elapsed_accounting_for_freeze(self.normal_resonance_time) < 5:
            while self.crisis_time_left() > 0:
                self.check_combat()
                self.click()
                self.task.next_frame()
        else:
            self.normal_resonance_time = -1
            self.wait_resonance_not_gray()

    def decide_teammate(self):
        # 满焰光: 1.0, 菲比一套: 0.95, 菲比一套(排除1点光燥): 0.90, 参考b站视频光主一套 0.69
        for _, char in enumerate(self.task.chars):
            self.logger.debug(f'zani teammate char: {char.char_name}')
            if char.char_name == 'char_phoebe':
                self.char_phoebe = char
                self.blazes_threshold = 0.4
                return
        self.blazes_threshold = 0.69
        return 
    
    def update_blazes(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 1627, 2014, 2176, 2017, name='zani_blazes', hcenter=True)
        blazes_percent = self.task.calculate_color_percentage(zani_blazes_color, box)
        blazes_percent = Decimal(str(blazes_percent)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.blazes = blazes_percent
        self.logger.debug(f'blazes_percent {blazes_percent}')
    
    def is_prepared(self):
        self.update_blazes()
        if self.blazes >= self.blazes_threshold:
            return True
        return False

    def wait_resonance_not_gray(self, timeout=5):
        start = time.time()
        while self.current_resonance() == 0 or self.has_cd('resonance'):
            self.check_combat()
            self.click()
            self.task.next_frame()
            if time.time() - start > timeout:
                self.logger.error('wait_resonance_not_gray timed out')

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if self.in_liberation:
            if self.liberation_time_left() < 1.7:
                return Priority.MAX
            elif has_intro and self.nightfall_time_left() > 0:
                self.logger.info(f'has_intro {has_intro}, wait nightfall end')
                while self.nightfall_time_left() > 0:
                    current_char.click()
                    self.task.next_frame()
            return 10000
        elif has_intro and self.crisis_time_left() > 0:
            return Priority.MIN + 1
        else:
            return super().do_get_switch_priority(current_char, has_intro)
        
    def has_long_actionbar(self):
        if self.check_liber():
            return True
        return False    
        
    def has_target(self,in_liber = False):
        if in_liber:
            outer_box = 'box_target_enemy_long'
            inner_box = 'box_target_enemy_long_inner'
        else:
            outer_box = 'box_target_enemy'
            inner_box = 'box_target_enemy_inner'
        aim_percent = self.task.calculate_color_percentage(aim_color, self.task.get_box_by_name(outer_box))
        aim_inner_percent = self.task.calculate_color_percentage(aim_color, self.task.get_box_by_name(inner_box))
        if aim_percent - aim_inner_percent > 0.02:
            return True
        return False
           
    def check_liber(self):
        if not self.task.in_team_and_world():
            return self.in_liberation
        if self.has_target(self.in_liberation):
            pass
        elif self.has_target(not self.in_liberation):
            self.in_liberation = not self.in_liberation
        return self.in_liberation   
        
    def is_phoebe_complete(self):
        if self.char_phoebe is not None:
            if self.get_state() == 2:
                self.state = 0
                self.char_phoebe.reset_action()
            return self.char_phoebe.is_action_complete()
    
    def get_state(self):
        if self.state == 1 and self.liberation_time_left() <= 0:
            self.state = 2
        return self.state
    
zani_light_color = {
    'r': (245, 255),  # Red range
    'g': (245, 255),  # Green range
    'b': (205, 225)  # Blue range
}

zani_blazes_color = {
    'r': (236, 252),  # Red range
    'g': (244, 255),  # Green range
    'b': (176, 196)   # Blue range
}