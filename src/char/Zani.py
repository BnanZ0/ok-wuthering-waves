import time
from decimal import Decimal, ROUND_HALF_UP

from src.char.BaseChar import BaseChar, Priority
from src.combat.CombatCheck import aim_color
from src.char.BaseChar import forte_white_color

class Zani(BaseChar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.liberaction_time = 0
        self.nightfall_time = 0
        self.crisis_time = 0
        self.is_crisis_active = False
        self.blaze = -1
        self.blaze_threshold = 0
        self.in_liberation = False
        self.liberation_allowed = False
        self.liberation2 = False
        self.first_nightfall = True
        self.char_phoebe = None
        
    def reset_state(self):
        super().reset_state()
        self.liberaction_time = 0
        self.nightfall_time = 0
        self.crisis_time = 0
        self.is_crisis_active = False
        self.blaze = -1
        self.blaze_threshold = 0
        self.in_liberation = False
        self.liberation_allowed = False
        self.liberation2 = False
        self.char_phoebe = None

    def do_perform(self):
        if self.blaze_threshold == 0:
            self.decide_teammate()
        if self.has_intro:
            self.logger.debug(f'handle intro')
            self.continues_normal_attack(1.4)
        self.check_liber()

        if self.in_liberation:
            self.logger.debug(f'in_liberation')
            if not self.should_end_liberation():
                if not self.liberation2:
                    self.logger.debug(f'other nightfall')
                    self.nightfall_combo()
            if self.in_liberation and self.liberation2 and self.click_liber2():
                return
            return self.switch_next_char()
        
        if self.is_crisis_active:
            while self.crisis_time_left() > 0:
                self.check_combat()
                self.click()
                self.task.next_frame()
            self.is_crisis_active = False
            if not self.liberation_allowed and self.liberation_available():
                self.liberation_allowed = True

        if self.liberation_allowed:
            self.logger.debug(f'liberation_allowed')
            self.liberation_allowed = False
            if self.click_liberation():
                self.in_liberation = True
                self.first_nightfall = True
                self.liberation2 = False
                self.liberaction_time = time.time()
                self.check_liber()
                self.continues_right_click(0.1)
                self.continues_normal_attack(0.1)
                #三终夜轮椅轴
                self.logger.debug(f'first nightfall')
                self.nightfall_combo()
                self.sleep(0.1)
                self.logger.debug(f'second nightfall')
                self.nightfall_combo()
                return self.switch_next_char()

        if self.echo_available():
            self.click_echo()

        if (self.get_zani_blazes() < self.blaze_threshold
            and not self.is_phoebe_complete()
        ):
            self.logger.debug(f'blazes not enough')
            if not self.standard_defense_protocol_combo():
                self.continues_normal_attack(0.1)
            if self.current_liberation() == 0 and self.is_forte_full():
                self.click_resonance()
            return self.switch_next_char()

        if ((self.get_zani_blazes() >= self.blaze_threshold 
            and not self.in_liberation)
            or self.is_phoebe_complete()
        ):
            if self.liberation_available():
                self.crisis_response_protocol_combo()
            else:
                self.logger.debug(f'everything is set but no liberation')
                self.crisis_response_protocol_combo(liberation_after_crisis=False)
            return self.switch_next_char()
        
        self.continues_normal_attack(1)
        self.switch_next_char()          

    def is_phoebe_complete(self):
        if self.char_phoebe is not None:
            self.logger.debug(f'phoebe action complete: {self.char_phoebe.is_action_complete}')
            if self.char_phoebe.is_action_complete:
                return True
        return False

    def standard_defense_protocol_combo(self):
        if self.is_forte_full():
            return False
        if self.resonance_available():
            self.send_resonance_key()
            self.sleep(0.1)
            self.continues_normal_attack(0.1)
            return True
        return False
    
    def crisis_response_protocol_combo(self, liberation_after_crisis=True):
        self.logger.debug(f'perform crisis_response_protocol')
        if not self.is_forte_full():
            if self.resonance_available():
                self.send_resonance_key()
                self.sleep(0.1)
                self.continues_normal_attack(0.1)
            else:
                self.heavy_attack(duration=0.6)
                self.sleep(0.55)
                self.continues_normal_attack(0.1)
            self.sleep(1.2)
            self.click()
            start = time.time()
            while time.time() - start < 1.9:
                if self.is_forte_full():
                    break
                self.check_combat()
                self.task.next_frame()
            start = time.time()
            while not self.is_forte_full():
                self.check_combat()
                self.click()
                self.task.next_frame()
        self.sleep(0.1)
        while self.is_forte_full():
            self.check_combat()
            self.send_resonance_key()
            self.task.next_frame()
        if liberation_after_crisis:
            self.liberation_allowed = True
        elif self.liberation_available():
            self.liberation_allowed = True

        self.crisis_time = time.time()
        self.is_crisis_active = True
    
    def get_zani_forte(self):           
        box = self.task.box_of_screen_scaled(3840, 2160, 1628, 1997, 2183, 2003, name='zani_forte', hcenter=True)
        forte_percent = 0
        forte_percent = self.task.calculate_color_percentage(zani_forte_color, box)
        forte_percent = Decimal(str(forte_percent)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.logger.debug(f'forte_percent {forte_percent}')
        return forte_percent

    def get_zani_blazes(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 1628, 2014, 2183, 2020, name='zani_blazes', hcenter=True)
        blazes_percent = 0
        blazes_percent = self.task.calculate_color_percentage(zani_blazes_color, box)
        blazes_percent = Decimal(str(blazes_percent)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.blaze = blazes_percent
        self.logger.debug(f'blazes_percent {blazes_percent}')
        return blazes_percent
    
    def is_nightfall_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2680, 1845, 2862, 2025, name='zani_attack', hcenter=True)
        light_percent = self.task.calculate_color_percentage(zani_light_color, box)
        self.logger.debug(f'nightfall_percent {light_percent}')
        if light_percent > 0.05:
            return True
        return False
    
    def should_end_liberation(self, check_forte=True):
        if self.liberation_elapsed() > 18:
            self.logger.info(f'liberation is about to end, perform liberation2')
            self.liberation2 = True
            return True
        if check_forte:
            self.wait_resonance_not_gray()
            if not self.is_forte_full():
                self.logger.info(f'Cannot perform another nightfall end liberation')
                self.liberation2 = True
                return True
        return False
        
    def nightfall_combo(self):
        self.logger.info(f'perform nightfall_combo')
        start = time.time()
        if not self.is_nightfall_ready():
            while not self.is_nightfall_ready() or time.time() - start < 1.6:
                self.check_combat()
                if (time.time() - start > 3.5 
                    or not self.in_liberation
                    or self.should_end_liberation(check_forte=False)
                ):
                    return
                self.click()
                self.task.next_frame()
        self.continues_normal_attack(0.4)
        if self.first_nightfall:
            self.logger.debug(f'cancel first nightfall')
            self.first_nightfall = False
            while self.is_nightfall_ready():
                self.check_combat()
                self.click()
                self.task.next_frame()
            self.sleep(0.1)
            self.continues_right_click(0.1)
        else:
            self.nightfall_time = time.time()
    
    def nightfall_time_left(self):
        #1.6
        self.logger.debug(f'nightfall_time: {self.nightfall_time}')
        if self.nightfall_time == 0:
            return 0
        result = 1.8 - self.all_time_elapsed_accounting_for_freeze(self.nightfall_time, intro_freeze=True)
        self.logger.debug(f'nightfall_time_left: {result}')
        return result
    
    def crisis_time_left(self):
        #1.5
        if self.crisis_time == 0 or not self.is_crisis_active:
            return 0
        result = 1.7 - self.all_time_elapsed_accounting_for_freeze(self.crisis_time, intro_freeze=True)
        self.logger.debug(f'crisis_time_left: {result}')
        return result
    
    def liberation_elapsed(self):
        if not self.in_liberation or self.liberaction_time == 0:
            return -1
        result = self.all_time_elapsed_accounting_for_freeze(self.liberaction_time)
        self.logger.debug(f'liberation_lasted: {result}')
        return result
    
    def click_liber2(self, switch_char=True):
        if self.liberation_available():   
            start = time.time()
            self.send_liberation_key()
            self.check_liber()
            if self.in_liberation:
                self.task.in_liberation = True
                if switch_char:
                    self.switch_next_char()
                if time.time() - start > 2:
                    self.add_freeze_duration(start, time.time()-start)
                    self.logger.debug(f'Zani click liber2 in {time.time()-start}')
                    self.blaze = -1
                    self.in_liberation = False
                    self.liberation_allowed = False
                self.task.in_liberation = False
                return True
            return False

    def wait_resonance_not_gray(self, timeout=5):
        #常态 0.16 解放 0.24
        start = time.time()
        while self.current_resonance() == 0 or self.has_cd('resonance'):
            self.check_combat()
            self.click()
            self.task.next_frame()
            if time.time() - start > timeout:
                self.logger.error('wait_resonance_not_gray timed out')

    def on_pause_switching(self):
        if self.liberation_elapsed() > 18:
            self.click_liber2(switch_char=False)

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if self.in_liberation:
            if self.liberation_elapsed() > 18:
                return Priority.MAX
            if has_intro and self.nightfall_time_left() > 0:
                self.logger.debug(f'zani_intro_wait_for_nightfall')
                condition = lambda: self.nightfall_time_left() > 0
                self.handle_pause_switching(current_char, condition)
            return 10000
        elif self.liberation_allowed:
            if has_intro:
                self.logger.debug(f'zani_intro_wait_for_crisis')
                condition = lambda: self.crisis_time_left() > 0
                self.handle_pause_switching(current_char, condition)
            return Priority.MAX
        else:
            return super().do_get_switch_priority(current_char, has_intro)
        
    def has_long_actionbar(self):
        if self.check_liber():
            return True
        return False
        
    def resonance_until_not_light(self):
        start = time.time()
        b = False
        while self.current_resonance() and not self.has_cd('resonance'):
            self.send_resonance_key()            
            b = True
            if time.time() - start > 1:
                return False
            self.check_combat()
            self.task.next_frame()
        return b
            
    def resonance_light(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 3105, 1845, 3285, 2010, name='zani_resonance', hcenter=True)
        light_percent = self.task.calculate_color_percentage(zani_light_color, box)
        return light_percent > 0.005  
            
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
        if self.has_target(self.in_liberation):
            return self.in_liberation

        """ if not self.in_liberation:
            self.logger.debug("Rechecking in_liberation state")
            self.sleep(0.1, False)
            if self.has_target(self.in_liberation):
                return self.in_liberation """
        self.sleep(0.1, False)
        if self.has_target(not self.in_liberation):
            self.in_liberation = not self.in_liberation
        return self.in_liberation       

    def decide_teammate(self):
        # 满焰光: 0.741, 菲比一套: 0.709, 菲比一套(排除1点光燥): 0.672, 参考b站视频光主一套 0.518
        for i, char in enumerate(self.task.chars):
            self.logger.debug(f'zani teammate char: {char.char_name}')
            if char.char_name == 'char_phoebe':
                self.char_phoebe = char
                self.logger.debug(f'zani blaze set to high value')
                self.blaze_threshold = 0.66
                return
        self.blaze_threshold = 0.5
        return 
        
    def is_forte_full(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2285, 1990, 2315, 2020, name='forte_full', hcenter=True)
        white_percent = self.task.calculate_color_percentage(forte_white_color, box)
        self.logger.debug(f'forte_white_percent {white_percent}')
        return white_percent > 0.28   
        
zani_light_color = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (195, 225)  # Blue range
}  

zani_forte_color = {
    'r': (239, 255),  # Red range
    'g': (222, 255),  # Green range
    'b': (157, 185)   # Blue range
} 

zani_blazes_color = {
    'r': (239, 247),  # Red range
    'g': (247, 255),  # Green range
    'b': (177, 187)   # Blue range
}