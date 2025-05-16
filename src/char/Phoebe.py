import time
import cv2
import numpy as np
from src.char.BaseChar import BaseChar, Priority
from src.char.Healer import Healer
from ok import color_range_to_bound

class Phoebe(BaseChar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intro_motion_freeze_duration = 0.9
        self.perform_intro = 0
        self.attribute = 0
        self.star_available = False
        self.char_zani = None
        self.state = {
            "starflash_combo": 0,
            "liberation": 0
        }
        
    def reset_state(self):
        super().reset_state()
        self.perform_intro = 0
        self.attribute = 0
        self.star_available = False
        self.char_zani = None
        self.state = {
            "starflash_combo": 0,
            "liberation": 0
        }

    def flying(self):
        return self.current_resonance() == 0 or self.current_echo() == 0

    def do_perform(self):
        start = time.time()
        if self.attribute == 0:
            self.decide_teammate()
        if self.has_intro:
            self.continues_normal_attack(1.5)
        else:
            self.sleep(0.01)

        if self.attribute == 1:
            self.click_echo()
        if self.flying():
            self.logger.info('Pheobe flying')
            self.continues_normal_attack(0.1)
            return self.switch_next_char()
        
        if self.is_action_complete():
            result = self.get_zani_state()
            if result == 1:
                self.logger.info('stop applying spectro frazzle')
                if not self.char_zani.liberation_time_left() < 1.7:
                    if self.resonance_available():
                        self.click_resonance(send_click=False)
                    else:
                        self.continues_normal_attack(1)
                return self.switch_next_char()
            elif result == 2:
                self.char_zani.state = 0
                self.reset_action()
        else:
            if (self.state["starflash_combo"] >= 2
                and self.state["liberation"] == 0 
                and self.liberation_available() 
                and self.click_liberation(send_click=False)
            ):
                self.state["liberation"] += 1
                self.click_resonance(send_click=False)
                return self.switch_next_char()
        
        wait_ui_time = 0.35 - (time.time() - start)
        if wait_ui_time > 0 and self.star_available and self.judge_forte() == 0:
            self.logger.debug('wait for UI')
            self.continues_normal_attack(wait_ui_time)

        starflash = self.absolution_or_confession()
        if self.liberation_available():
            if self.click_liberation(send_click=True):
                self.state["liberation"] += 1
                self.sleep(0.1)
        if starflash or self.judge_forte() > 0 or self.heavy_attack_ready():
            self.starflash_combo()  
        if self.resonance_available():
            if self.attribute == 2:
                self.click_resonance_once()
            else:
                self.click_resonance()
            return self.switch_next_char()
        self.continues_normal_attack(0.1)
        self.switch_next_char()
  
    def reset_action(self):
        self.state["liberation"] = 0
        self.state["starflash_combo"] = 0

    def judge_forte(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 1633, 2004, 2160, 2014, name='phoebe_forte1', hcenter=True)
        forte = self.calculate_forte_num(phoebe_forte_blue_color,box,2,18,20,50)
        if forte > 0:
            return forte
        forte = self.calculate_forte_num(phoebe_forte_light_color,box,4,9,11,25)
        return forte
            
    def starflash_combo(self):
        self.logger.info('perform starflash_combo')
        start = time.time()
        check_forte = start
        if not self.heavy_attack_ready():
            while not self.heavy_attack_ready():
                self.click()
                if time.time() - start > 5:
                    return
                if time.time() - check_forte > 1 and self.judge_forte() == 0:                
                    return
                else:
                    check_forte = time.time()
                self.task.next_frame()
        self.logger.info('perform heavy_attack')
        self.perform_heavy_attack()
        if not self.is_forte_full():
            self.state["starflash_combo"] += 1
                
    def perform_heavy_attack(self):   
        if not self.absolution_or_confession():
            start = time.time()
            while self.is_forte_full():
                self.check_combat()
                self.heavy_attack(duration=0.3)
                if time.time() - start > 2.5:
                    break
                self.sleep(0.3)

    def click_resonance_once(self):
        start = time.time()
        while self.resonance_available():
            self.check_combat()
            if time.time() - start > 0.5:
                return True
            self.send_resonance_key()
            self.task.next_frame()
        return False
    
    def confession_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 3149, 1832, 3225, 1857, name='phoebe_resonance', hcenter=False)
        blue_percent = self.task.calculate_color_percentage(pheobe_litany_blue_color, box)
        self.logger.debug(f'blue_percent {blue_percent}')
        return blue_percent > 0.15        

    def heavy_attack_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 2740, 1832, 2803, 1857, name='phoebe_attack', hcenter=False)
        light_percent = self.task.calculate_color_percentage(phoebe_light_color, box)
        self.logger.debug(f'light_percent {light_percent}')
        if light_percent > 0.15 and self.is_forte_full():
            return True
        blue_percent = self.task.calculate_color_percentage(phoebe_blue_color, box)
        return blue_percent > 0.15 and self.is_forte_full()
    
    def absolution_or_confession(self):
        self.task.wait_in_team_and_world(time_out=3, raise_if_not_found=False)
        condition = lambda: False
        if not self.star_available and not self.check_middle_star():
            condition = lambda: self.is_forte_full()
        elif self.confession_ready() and self.judge_forte() == 0:
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
            self.continues_right_click(0.1)
            return True
        return False
                    
    def has_long_actionbar(self):
        return True
        
    def switch_next_char(self, *args):
        if self.is_con_full():
            if self.attribute == 2:
                self.click_echo()
            self.perform_intro = time.time()
        
        return super().switch_next_char(*args)
        
    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if self.attribute == 2 and self.get_zani_state() == 1 and not self.is_action_complete():
            return 10000
        if self.attribute == 2 and self.get_zani_state() == 2 and isinstance(current_char, Healer):
            return 10000
        if self.total_time_elapsed_accounting_for_freeze(self.perform_intro, intro_freeze=True) < 4.5:
            return Priority.MIN + 1
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
    
    def judge_frequncy_and_amplitude(self, gray, min_freq, max_freq, min_amp):
        height, width = gray.shape[:]
        if height == 0 or width < 64 or not np.array_equal(np.unique(gray), [0, 255]):
            return 0       

        white_ratio = np.count_nonzero(gray == 255) / gray.size
        profile = np.sum(gray == 255, axis=0).astype(np.float32)
        profile -= np.mean(profile)
        n = np.abs(np.fft.fft(profile))
        amplitude = 0
        frequncy = 0
        i = 1
        while i < width:
            if n[i]> amplitude:
                amplitude = n[i]
                frequncy = i
            i+=1
        return (min_freq <= i <= max_freq) or amplitude >= min_amp
        
    def calculate_forte_num(self, forte_color, box, num = 1, min_freq = 39, max_freq = 41, min_amp = 50):
        cropped = box.crop_frame(self.task.frame)
        lower_bound, upper_bound = color_range_to_bound(forte_color)
        image = cv2.inRange(cropped, lower_bound, upper_bound)
        
        forte = 0
        height, width = image.shape
        step = int(width / num)
        left = 0
        fail_count = 0
        warning = False
        while left+step < width:
            gray = image[:,left:left+step] 
            score = self.judge_frequncy_and_amplitude(gray,min_freq,max_freq,min_amp)
            if fail_count == 0:
                if score:
                    forte += 1
                else:
                    fail_count+=1
            else:
                if score:
                    warning = True
                else:
                    fail_count+=1
            left+=step
        if warning:
            self.logger.debug('Frequncy analysis error, return the forte before mistake.')
        self.logger.debug(f'Frequncy analysis with forte {forte}')    
        return forte
  
    def get_zani_state(self):
        if self.attribute == 2 and self.char_zani is not None:
            return self.char_zani.get_state()
    
    def is_action_complete(self):
        if self.attribute != 2:
            return False
        self.logger.debug(f'state_liberation {self.state["liberation"]} state_starflash_combo {self.state["starflash_combo"]}')
        if self.state["liberation"] >= 1 and self.state["starflash_combo"] >= 2:
            return True
        if self.is_current_char and not self.liberation_available() and self.judge_forte() == 0 and not self.confession_ready():
            return True
        return False

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
    'r': (225, 255),  # Red range
    'g': (225, 255),  # Green range
    'b': (190, 225)   # Blue range
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