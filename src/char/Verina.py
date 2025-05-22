import time
import cv2
import numpy as np

from src.char.Healer import Healer
from ok import color_range_to_bound

class Verina(Healer):
    def count_liberation_priority(self):
        return 2
    
    def do_perform(self):
        if self.has_intro:
            self.wait_intro(click=False, time_out=1.1)
        else:
            self.sleep(0.01)
        if self.flying():
            self.logger.info('Verina flying')
            self.normal_attack()
            return self.switch_next_char()
        
        do_con_full = self.total_time_elapsed_accounting_for_freeze(self.perform_outro_time) >= 30
        if do_con_full:
            if self.judge_forte() < 2 and not self.is_con_full():
                self.continues_normal_attack(1.5)
            else:
                self.continues_normal_attack(0.1)

        self.click_resonance()
        self.click_echo()
        if self.liberation_available():
            self.click_liberation()
        if do_con_full:
            expectation_con = self.judge_forte() * 0.125 + self.get_current_con()
            if expectation_con >= 1 and not self.is_con_full():
                #self.heavy_attack()
                self.task.send_key('SPACE')
                self.sleep(0.15)
                start = time.time()
                while time.time() - start < 1:
                    self.task.click(interval=0.1)
                    if self.is_con_full():
                        break
                    if not self.is_forte_full():
                        self.sleep(0.1)
                        break
        self.switch_next_char()

    def judge_forte(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 1628, 2004, 2160, 2014, name='verina_forte', hcenter=True)
        self.task.draw_boxes(box.name, box)
        forte = self.calculate_forte_num(verina_forte_light_color,box,4,18,20,50)
        return forte
    
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
    
verina_forte_light_color = {
    'r': (250, 255),  # Red range
    'g': (238, 255),  # Green range
    'b': (112, 121)   # Blue range
}  