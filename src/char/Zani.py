import time
from decimal import Decimal, ROUND_HALF_UP

from src.char.BaseChar import BaseChar, Priority
from src.combat.CombatCheck import aim_color
from src.char.BaseChar import forte_white_color

class Zani(BaseChar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.liberation_time = 0
        self.in_liberation = False
        self.have_forte = False
        self.last_attack = 0
        self.final_attack = False
        self.blazes = -1
        self.blazes_threshold = -1
        self.char_phoebe = None
        self.crisis_time = -1
        self.nightfall_time = -1
        
    def reset_state(self):
        self.last_attack = 0
        super().reset_state()
        
    def do_perform(self): 
        if self.blazes_threshold == -1:
            self.decide_teammate()

        if self.has_intro:
            self.continues_normal_attack(1.5)
        self.check_liber()
        if self.echo_available():
            self.click_echo()

        if self.in_liberation:
            self.logger.debug(f'in_liberation')
            if self.should_end_liberation():
                if self.click_liber2():
                    return
            else:
                self.logger.debug(f'other nightfall')
                self.nightfall_combo()
            return self.switch_next_char()

        if self.crisis_time > 0:
            self.wait_for_crisis_protocol_end()

        cast_liberation = False
        if self.is_prepared() or self.is_phoebe_complete():
            self.crisis_response_protocol_combo()
            if self.liberation_available():
                cast_liberation = True
                if self.blazes != 1:
                    self.wait_for_crisis_protocol_end()
            else:
                return self.switch_next_char()

        if cast_liberation:
            self.logger.debug(f'cast_liberation')
            cast_liberation = False
            if self.click_liberation():
                self.in_liberation = True
                self.liberation_time = time.time()
                self.check_liber()
                self.continues_right_click(0.1)
                self.continues_normal_attack(0.1)
                self.logger.debug(f'first nightfall')
                self.nightfall_combo(cancel_last_smash = True)
                self.sleep(0.1)
                self.logger.debug(f'second nightfall')
                self.nightfall_combo()
                return self.switch_next_char()
        
        if not self.is_phoebe_complete():
            if not self.standard_defense_protocol_combo():
                self.continues_normal_attack(0.1)
            if not self.liberation_available() and self.is_forte_full():
                self.crisis_response_protocol_combo()
            return self.switch_next_char()

        """ shield_attack = False
        if self.has_intro:
            self.continues_normal_attack(1.5)
        elif self.in_liberation:
            shield_attack = self.time_elapsed_accounting_for_freeze(self.last_attack) > 3
        self.check_liber()
        self.click_echo() 
        if self.in_liberation and self.liberation2_ready():          
            start = time.time()
            self.click_liberation()
            self.check_liber()
            if self.in_liberation:
                self.switch_next_char()
                if time.time() - start > 2:
                    self.add_freeze_duration(start, time.time()-start)
                    self.logger.info(f'Zani click liber2 in {time.time()-start}')  
                    self.in_liberation = False
                return
        if not self.in_liberation and self.resonance_available(): 
            if not self.resonance_until_not_light():
                self.logger.info('res+liber combo failed')
            self.continues_normal_attack(0.55)
        if not self.in_liberation and self.liberation_available():
            if self.click_liberation():
                self.in_liberation = True
                self.have_forte = True
                self.liberaction_time = time.time()
                self.last_attack = self.liberaction_time
                self.continues_normal_attack(1.1)
                self.logger.info('Zani click liber1.')   
                return self.switch_next_char()
        if self.in_liberation:
            self.last_attack = time.time()
    #开大时，zani离场再登场的平a，会打出普通攻击而不是强化攻击
    #算是bug，目前先延迟0.3秒，等kl修
            if shield_attack and not (self.final_attack or self.attack_light()):
                self.continues_normal_attack(0.3)
            self.continues_normal_attack(0.6)
            return self.switch_next_char()              
        self.continues_normal_attack(0.1) """
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
                self.task.in_liberation = False
                return True
        return False
        
    def should_end_liberation(self, check_forte=True):
        result = self.total_time_elapsed_accounting_for_freeze(self.liberation_time)
        self.logger.debug(f'liberation_lasted: {result}')
        if self.liberation_elapsed() > 18.3:
            self.logger.info(f'liberation is about to end, perform liberation2')
            return True
        if self.is_nightfall_ready():
            return False
        if check_forte:
            self.wait_resonance_not_gray()
            if not self.is_forte_full():
                self.logger.info(f'Cannot perform another nightfall end liberation')
                return True
        return False
    
    def liberation_elapsed(self):
        if not self.in_liberation or self.liberation_time <= 0:
            return -1
        result = self.time_elapsed_accounting_for_freeze(self.liberation_time)
        self.logger.debug(f'liberation_lasted: {result}')
        return result
    
    def nightfall_combo(self, cancel_last_smash = False):
        self.logger.info(f'perform nightfall_combo')
        start = time.time()
        if not self.is_nightfall_ready():
            while not self.is_nightfall_ready() or time.time() - start < 1.6:
                self.click()
                if (time.time() - start > 3.5 
                    or not self.in_liberation
                    or self.should_end_liberation(check_forte=False)
                ):
                    return
                self.check_liber()
                self.check_combat()
                self.task.next_frame()
        self.continues_normal_attack(0.5)
        if cancel_last_smash:
            self.logger.debug(f'cancel nightfall')
            while self.is_nightfall_ready():
                self.check_combat()
                self.click()
                self.task.next_frame()
            self.sleep(0.1)
            self.continues_right_click(0.1)
        else:
            self.nightfall_time = time.time()

    def is_nightfall_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2680, 1845, 2862, 2025, name='zani_attack', hcenter=True)
        light_percent = self.task.calculate_color_percentage(zani_light_color, box)
        self.logger.debug(f'nightfall_percent {light_percent}')
        if light_percent > 0.05:
            return True
        return False
    
    def nightfall_time_left(self):
        #1.6
        result = 1.8 - self.time_elapsed_accounting_for_freeze(self.nightfall_time)
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
            self.send_resonance_key()
            self.normal_resonance_time = time.time()
            self.sleep(0.1)
            self.continues_normal_attack(0.1)
            return True
        return False
    
    def crisis_response_protocol_combo(self):
        self.logger.debug(f'perform crisis_response_protocol')
        if not self.is_forte_full():
            if not self.standard_defense_protocol_combo():
                self.heavy_attack(duration=0.6)
                self.sleep(0.55)
                self.continues_normal_attack(0.1)
            if not self.is_forte_full():
                self.sleep(1.2)
            self.click()
            start = time.time()
            while time.time() - start < 1.9:
                if self.is_forte_full():
                    break
                self.check_combat()
                self.task.next_frame()
            while not self.is_forte_full():
                self.click()
                self.check_combat()
                self.task.next_frame()
            self.sleep(0.1)
        while self.is_forte_full():
            self.check_combat()
            self.send_resonance_key()
            self.task.next_frame()
        self.crisis_time = time.time()

    def crisis_time_left(self):
        #1.5秒
        result = 1.7 - self.time_elapsed_accounting_for_freeze(self.crisis_time)
        if result <= 0:
            self.crisis_time = -1
            return 0
        self.logger.debug(f'crisis_time_left: {result}')
        return result
    
    def wait_for_crisis_protocol_end(self):
        if self.time_elapsed_accounting_for_freeze(self.normal_resonance_time) < 5:
            while self.crisis_time_left() > 0:
                self.check_combat()
                self.click()
                self.task.next_frame()
        else:
            self.crisis_time = -1
            self.wait_resonance_not_gray()

    def decide_teammate(self):
        # 满焰光: 1.0, 菲比一套: 0.95, 菲比一套(排除1点光燥): 0.90, 参考b站视频光主一套 0.69
        for i, char in enumerate(self.task.chars):
            self.logger.debug(f'zani teammate char: {char.char_name}')
            if char.char_name == 'char_phoebe':
                self.char_phoebe = char
                self.logger.debug(f'zani blaze set to high value')
                self.blazes_threshold = 0.95
                return
        self.blazes_threshold = 0.69
        return 
    
    def update_blazes(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 1627, 2014, 2176, 2017, name='zani_blazes', hcenter=True)
        blazes_percent = self.task.calculate_color_percentage(zani_blazes_color, box)
        blazes_percent = Decimal(str(blazes_percent)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.blazes = blazes_percent
        self.logger.debug(f'blazes_percent {blazes_percent}')
    
    def is_phoebe_complete(self):
        if self.char_phoebe is not None:
            self.logger.debug(f'phoebe action complete: {self.char_phoebe.is_action_complete}')
            if self.char_phoebe.is_action_complete:
                return True
        return False

    def is_prepared(self):
        self.update_blazes()
        if self.blazes >= self.blazes_threshold:
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

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if self.in_liberation:
            if self.liberation_elapsed() > 18.3:
                return Priority.MAX
            elif self.has_intro and self.nightfall_time_left() > 0:
                while self.nightfall_time_left() > 0:
                    current_char.click()
                    self.task.next_frame()
            return 10000
        elif self.has_intro and self.crisis_time_left() > 0:
            return Priority.MIN + 1
        else:
            return super().do_get_switch_priority(current_char, has_intro)
    #未使用
    def liberation2_ready(self):
        if not self.liberation_available(): 
            return False
        if (self.have_forte and self.final_attack) or self.attack_light():
            return False
        if self.time_elapsed_accounting_for_freeze(self.liberation_time) > 18.3:
            return True
        if not self.have_forte and self.time_elapsed_accounting_for_freeze(self.liberation_time) > 12:
            return True
        return False
        
    def has_long_actionbar(self):
        if self.check_liber():
            return True
        return False
    #未使用
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
    #未使用
    def attack_light(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2690, 1845, 2860, 2010, name='zani_attack', hcenter=False)
        light_percent = self.task.calculate_color_percentage(zani_light_color, box)
        return light_percent > 0.01        
        
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
            pass
        else:
            self.in_liberation = not self.in_liberation
        return self.in_liberation        
           
    def switch_next_char(self, *args):
        self.have_forte = self.is_forte_full()
        if self.in_liberation:
            if self.attack_light():
                self.final_attack = False
            else:
                self.final_attack = not self.final_attack
        else:
            self.final_attack = False
        return super().switch_next_char(*args)
        
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