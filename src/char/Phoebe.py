import time

from src.char.BaseChar import BaseChar, Priority
from src.char.Healer import Healer

class Phoebe(BaseChar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perform_outro_time = 0
        self.resonance_time = 0
        self.attribute = 0
        self.star_available = False
        self.char_zani = None
        self.starflash_combo_count = 0
        self.is_action_complete = False
        
    def reset_state(self):
        super().reset_state()
        self.perform_outro_time = 0
        self.resonance_time = 0
        self.attribute = 0
        self.star_available = False
        self.char_zani = None
        self.starflash_combo_count = 0
        self.is_action_complete = False
    
    def flying(self):
        return self.current_resonance() == 0 or self.current_echo() == 0

    def do_perform(self):
        start = time.time()
        if self.attribute == 0:
            self.decide_teammate()
        if self.has_intro:
            self.continues_normal_attack(1.5)
        if self.flying():
            self.logger.info('Pheobe flying')
            self.continues_normal_attack(0.1)
            return self.switch_next_char()
        
        if self.is_zani_ready():
            self.logger.debug('stop applying spectro frazzle')
            if not self.char_zani.liberation_elapsed() > 18:
                if self.resonance_available():
                    self.click_resonance_once()
                else:
                    self.continues_normal_attack(1.4)
            return self.switch_next_char()
        
        if not self.check_middle_star():
            self.absolution_or_confession()
        elif not self.in_absolution_or_confession():
            self.logger.debug('wait for UI')
            wait_ui_time = 0.4 - (time.time() - start)
            if wait_ui_time > 0:
                self.continues_normal_attack(wait_ui_time)
        
        if self.attribute == 1:
            self.click_echo()

        self.absolution_or_confession()
        if self.star_available and self.liberation_available():
            self.click_liberation()
            if self.starflash_combo(): 
                return self.switch_next_char()
        if self.resonance_available():
            self.logger.debug('click_resonance_once')
            if self.resonance_time > 0 and self.total_time_elapsed_accounting_for_freeze(self.resonance_time) <= 11.4:
                self.starflash_combo()
                self.click_resonance_once()
                self.resonance_time = 0
            else:
                self.click_resonance_once()
                self.starflash_combo()
            return self.switch_next_char()   
        if self.in_absolution_or_confession():
            self.logger.debug('in_absolution_or_confession')
            self.starflash_combo()
        self.continues_normal_attack(0.1)
        self.switch_next_char()
        
    def starflash_combo(self):
        self.logger.debug('perform starflash_combo')
        self.task.wait_in_team_and_world(time_out=3, raise_if_not_found=False)
        if not self.in_absolution_or_confession() and not self.absolution_or_confession():
            return
        start = time.time()
        if not self.heavy_attack_ready():
            if not self.has_forte:
                return False
            while not self.heavy_attack_ready():
                self.click()
                if time.time() - start > 5:
                    break
                if time.time() - start > 0.5 and not self.in_absolution_or_confession():
                    if not self.absolution_or_confession():
                        return
                self.click()
                self.task.next_frame()
        self.perform_heavy_attack()
        if not self.is_forte_full():
            self.starflash_combo_count += 1
        if self.is_con_full() or self.liberation_available():
            self.sleep(0.3)
        return True
                
    def perform_heavy_attack(self):
        if not self.absolution_or_confession():
            start = time.time()
            while self.is_forte_full():
                self.check_combat()
                self.heavy_attack(duration=0.3)
                if time.time() - start > 2.5:
                    break
                self.task.next_frame()

    def click_resonance_once(self):
        start = time.time()
        while self.resonance_available():
            self.check_combat()
            if time.time() - start > 0.5:
                return True
            self.send_resonance_key()
            self.resonance_time = time.time()
            self.task.next_frame()
    
    def absolution_or_confession(self):
        self.task.wait_in_team_and_world(time_out=3, raise_if_not_found=False)
        condition = lambda: False
        if not self.star_available and self.is_forte_full():
            condition = lambda: self.is_forte_full()
        elif self.confession_ready():
            condition = lambda: self.confession_ready()

        if condition():
            if self.attribute == 2:
                self.task.send_key_down(self.get_resonance_key())
            else:
                self.task.mouse_down()
                
            start = time.time()
            while condition() or time.time() - start < 0.5:
                if time.time() - start > 1.2:
                    break
                self.task.next_frame()

            if self.attribute == 2:
                self.task.send_key_up(self.get_resonance_key())
                self.logger.info(f'Enters confession status')
            else:
                self.task.mouse_up()
                self.logger.info(f'Enters absolution status')
            
            self.star_available = True
            self.continues_right_click(0.1)
            self.starflash_combo_count = 0
            return True
        return False
    
    def confession_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 3149, 1832, 3225, 1857, name='phoebe_resonance', hcenter=True)
        blue_percent = self.task.calculate_color_percentage(phoebe_blue_color, box)
        self.logger.debug(f'resonance_blue_percent {blue_percent}')
        return blue_percent > 0.15        

    def heavy_attack_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2740, 1832, 2803, 1857, name='phoebe_attack', hcenter=False)
        light_percent = self.task.calculate_color_percentage(phoebe_light_color, box)
        self.logger.debug(f'attack_light_percent {light_percent}')
        if light_percent > 0.15 and self.is_forte_full():
            return True
        blue_percent = self.task.calculate_color_percentage(phoebe_blue_color, box)
        self.logger.debug(f'attack_blue_percent {light_percent}')
        return blue_percent > 0.15 and self.is_forte_full()
        
    def in_absolution_or_confession(self):           
        box = self.task.box_of_screen_scaled(3840, 2160, 1633, 1987, 1830, 2010, name='phoebe_forte', hcenter=True)
        forte_percent = self.task.calculate_color_percentage(phoebe_forte_light_color, box)
        if forte_percent > 0.03:
            self.logger.debug(f'in_absolution: {True}')
            return True
        forte_percent = self.task.calculate_color_percentage(phoebe_forte_blue_color, box) 
        self.logger.debug(f'in_confession: {forte_percent > 0.01}')
        return forte_percent > 0.03

    def update_current_status(self):
        if self.attribute == 2:
            times = 2
        else:
            times = 4
        if (self.star_available 
            and self.starflash_combo_count == times
            and not self.liberation_available()
        ):
            self.is_action_complete = True
        else:
            self.is_action_complete = False
        self.logger.debug(f'star_available: {self.star_available}')
        self.logger.debug(f'starflash_combo_count: {self.starflash_combo_count}')
        self.logger.debug(f'is_action_complete: {self.is_action_complete}')

    def has_long_actionbar(self):
        return True
        
    def is_zani_ready(self):
        if self.attribute == 2 and self.char_zani is not None:
            if (self.char_zani.in_liberation 
                or self.char_zani.liberation_allowed
                or self.char_zani.blaze >= self.char_zani.blaze_threshold
            ):
                return True
        return False
    
    def switch_next_char(self, *args):
        if not self.is_zani_ready():
            if self.liberation_available():
                self.click_liberation()
            self.update_current_status()
        if self.attribute == 2 and self.is_con_full():
            self.click_echo()
            self.sleep(0.05)
        return super().switch_next_char(*args)
        
    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        outro_lasted = self.total_time_elapsed_accounting_for_freeze(self.perform_outro_time, intro_freeze=True)
        self.logger.debug(f'phoebe outro lasted: {outro_lasted}')
        if outro_lasted < 4.0:
            return Priority.MIN
        elif (self.attribute == 2 
              and self.char_zani is not None 
              and not self.char_zani.in_liberation
              and isinstance(current_char, Healer)
            ):
            # 吃奶的延奏
            return Priority.MAX -1
        else:
            return super().do_get_switch_priority(current_char, has_intro)
            
    def check_middle_star(self):
        if self.star_available:
            return True
        box = self.task.box_of_screen_scaled(3840, 2160, 1890, 2010, 1930, 2030, name='phoebe_middle_star', hcenter=True)
        forte_percent = self.task.calculate_color_percentage(phiebe_star_light_cloor, box)
        self.logger.debug(f'middle_star_light_percent {forte_percent}')
        if forte_percent > 0.1:
            self.star_available = True
            return True
        forte_percent = self.task.calculate_color_percentage(phiebe_star_blue_cloor, box)
        self.logger.debug(f'middle_star_blue_percent {forte_percent}')
        if forte_percent > 0.1:
            self.star_available = True
            return True    
        return False
        
    def decide_teammate(self):
        for i, char in enumerate(self.task.chars):
            self.logger.debug(f'phoebe teammate char: {char.char_name}')
            if char.char_name == 'char_zani':
                self.logger.debug(f'phoebe set attribute: support')
                self.char_zani = self.task.chars[i]
                self.attribute = 2
                return
        self.logger.debug(f'phoebe set attribute: attacker')
        self.attribute = 1
        return 
    
  
phoebe_blue_color = {
    'r': (130, 170),  # Red range
    'g': (205, 235),  # Green range
    'b': (240, 255)   # Blue range
}  

pheobe_litany_blue_color = {
    'r': (115, 170),  # Red range
    'g': (160, 235),  # Green range
    'b': (230, 255)   # Blue range
}

phoebe_light_color = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (200, 230)   # Blue range
}  

phoebe_forte_light_color = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (165, 195)   # Blue range
}  

phoebe_forte_blue_color = {
    'r': (220, 250),  # Red range
    'g': (225, 255),  # Green range
    'b': (185, 215)   # Blue range
}  

phiebe_star_light_cloor = {
    'r': (235, 255),  # Red range
    'g': (220, 250),  # Green range
    'b': (160, 190)   # Blue range
}  

phiebe_star_blue_cloor = {
    'r': (240, 255),  # Red range
    'g': (240, 255),  # Green range
    'b': (240, 255)   # Blue range
}  