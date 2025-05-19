from src.char.Healer import Healer


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
        self.click_resonance()
        self.click_echo()
        liberated = self.click_liberation()
        if self.is_forte_full():
            self.heavy_attack()
        elif not liberated:
            self.click_liberation(wait_if_cd_ready=1, send_click=True)
        self.switch_next_char()
