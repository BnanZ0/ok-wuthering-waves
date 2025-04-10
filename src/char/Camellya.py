import time
from decimal import Decimal, ROUND_HALF_UP

from src.char.BaseChar import BaseChar, Priority


class Camellya(BaseChar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_heavy = 0
        self.heavy_attack_timer = False
        self.heavy_attack_timestamp = None

    def reset_state(self):
        super().reset_state()
        self.heavy_attack_timer = False
        self.heavy_attack_timestamp = None

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
            self.continues_normal_attack(1.2)
            self.sleep(0.1)
            self.camellya_heavy_attack(4.1, until_con_full=True)

        self.click_liberation(con_less_than=0.82)
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
                    self.check_combat()
                    self.send_resonance_key(post_sleep=1.2)
                    budding = True
                else:
                    self.click(interval=0.1)
                    current_con = self.get_current_con()
                    if current_con < 0.82:
                        self.click_resonance()
                        self.click_echo()
                        return self.switch_next_char()
                if budding:
                    self.logger.info(f'start budding')
                    self.check_combat()
                    budding_start_time = time.time()
                    loop_time = 5.1
            else:
                current_forte = self.get_camellya_forte(True)
                if not heavy_att:
                    heavy_att = True
                    self.task.mouse_down()
                if self.click_liberation() and heavy_att:
                    self.sleep(0.2)
                    self.task.mouse_down()
            self.check_target(heavy_att)
            self.task.next_frame()
            if heavy_att:
                self.heavy_attack_check(current_forte, True)
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
        self.logger.debug(f'red_percent {red_percent}')
        return red_percent > 0.12    
    
    def get_camellya_forte(self, budding=False):           
        box = self.task.box_of_screen_scaled(3840, 2160, 1628, 2002, 2183, 2008, name='camellya_forte', hcenter=True)
        forte_percent = 0
        if not budding:
            forte_percent = self.task.calculate_color_percentage(camellya_forte_color, box)
            self.logger.debug(f'forte_percent {forte_percent}')
        else:
            forte_percent = self.task.calculate_color_percentage(camellya_budding_forte_color, box)
            self.logger.debug(f'forte_percent_budding {forte_percent}')
        forte_percent = Decimal(str(forte_percent)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        return forte_percent
    
    def camellya_heavy_attack(self, duration, check_combat = True, until_con_full = False):
        self.task.mouse_down()
        start = time.time()
        while time.time() - start < duration:
            current_forte = self.get_camellya_forte()
            if current_forte <= 0.01:
                break
            if until_con_full and self.is_con_full():
                break
            if check_combat:
                self.check_target(True)
            self.task.next_frame()
            self.heavy_attack_check(current_forte)
        self.sleep(0.1)
        self.task.mouse_up()
        self.heavy_attack_timer = False

    def heavy_attack_check(self, current_forte = None, budding = False):
        if current_forte is None:
            return
        diff = current_forte - self.get_camellya_forte(budding)
        self.logger.debug(f'diff {diff}')
        if diff <= 0.002:
            if not self.heavy_attack_timer:
                self.heavy_attack_timer = True
                self.heavy_attack_timestamp = time.time()
        else:
            self.heavy_attack_timer = False
        if self.heavy_attack_timer and self.time_elapsed_accounting_for_freeze(self.heavy_attack_timestamp) > 0.7:
            self.logger.debug(f'retry heavy attack')
            self.task.mouse_up()
            self.sleep(0.1)
            self.task.mouse_down()
            self.sleep(0.1)
    
    def check_target(self, heavy_att = False):
        if not self.task.has_target():
            if heavy_att:
                self.task.mouse_up()
            self.check_combat()
            if heavy_att:
                self.sleep(0.1)
                self.task.mouse_down()
                self.sleep(0.1)

camellya_red_color = {
    'r': (200, 250),  # Red range
    'g': (60, 90),  # Green range
    'b': (150, 190)   # Blue range
} 

camellya_forte_color = {
    'r': (225, 265),  # Red range
    'g': (40, 68),  # Green range
    'b': (125, 149)   # Blue range
} 

camellya_budding_forte_color = {
    'r': (245, 265),  # Red range
    'g': (185, 210),  # Green range
    'b': (190, 225)   # Blue range
} 
