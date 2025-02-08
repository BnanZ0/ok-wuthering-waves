import time

from src.char.BaseChar import BaseChar, Priority


class Camellya(BaseChar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_heavy = 0

    def reset_state(self):
        super().reset_state()

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if has_intro:
            return Priority.MAX - 1
        else:
            return super().do_get_switch_priority(current_char, has_intro)

    def wait_resonance_not_gray(self, timeout=5):
        start = time.time()
        while self.current_resonance() == 0:
            self.click()
            self.sleep(0.1)
            if time.time() - start > timeout:
                self.logger.error('wait wait_resonance_not_gray timed out')

    def on_combat_end(self, chars):
        next_char = str((self.index + 1) % len(chars) + 1)
        self.logger.debug(f'Camellya on_combat_end {self.index} switch next char: {next_char}')
        start = time.time()
        while time.time() - start < 6:
            self.task.load_chars()
            current_char = self.task.get_current_char(raise_exception=False)
            if current_char and current_char.name != "Camellya":
                break
            else:
                self.task.send_key(next_char)
            self.sleep(0.2, False)
        self.logger.debug(f'Camellya on_combat_end {self.index} switch end')

    def do_perform(self):
        if self.has_intro:
            self.wait_intro(click=True)
            start = time.time()
            while time.time() - start < 8:
                if self.is_con_full():
                    break
                self.click(interval=0.1)
                self.check_combat()

        self.click_liberation(con_less_than=1)
        start_con = self.get_current_con()
        if start_con < 0.82:
            loop_time = 1.1
        else:
            loop_time = 4.1
        budding_start_time = time.time()
        budding = False
        heavy_att = False
        while time.time() - budding_start_time < loop_time or self.task.find_one('camellya_budding', threshold=0.7):
            if not budding:
                if self.ephemeral_ready():
                    self.send_resonance_key()
                    budding = True
                else:
                    self.click(interval=0.1)
                    current_con = self.get_current_con()
                    if current_con < 0.82:
                        self.send_resonance_key()
                        self.click_echo()
                        return self.switch_next_char()
                if budding:
                    self.sleep(1.2)
                    budding_start_time = time.time()
                    loop_time = 5.1
            else:
                if not heavy_att:
                    heavy_att = True
                    self.task.send_key('space')
                    if self.liberation_available():
                        self.click_liberation()
                    else:
                        self.task.mouse_down(key='right')
                        self.sleep(0.1,False)
                        self.task.mouse_up(key='right')
                        self.sleep(0.1,False)
                    self.task.mouse_down()
                if self.liberation_available():
                    self.click_liberation()
                    self.sleep(0.2)
                    if heavy_att:
                        self.task.mouse_down()
            if not self.task.in_combat():
                if heavy_att:
                    self.task.mouse_up()
                self.task.raise_not_in_combat('combat check not in combat')
            self.task.next_frame()
        if heavy_att:
            self.task.mouse_up()
            self.sleep(0.1)
        if budding:
            self.click_resonance()
        self.click_echo()
        self.switch_next_char()

    def click_echo(self, *args):
        if self.echo_available():
            self.send_echo_key()
            return True
        
    def ephemeral_ready(self):
        box = self.task.box_of_screen_scaled(3840, 2160, 3149, 1832, 3225, 1857, name='camellya_resonance', hcenter=True)
        red_percent = self.task.calculate_color_percentage(camellya_red_color, box)
        self.logger.info(f'red_percent {red_percent}')
        return red_percent > 0.12    
    
camellya_red_color = {
    'r': (200, 250),  # Red range
    'g': (60, 90),  # Green range
    'b': (150, 190)   # Blue range
}  
