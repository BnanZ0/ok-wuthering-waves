from src.char.BaseChar import BaseChar


class HavocRover(BaseChar):

    def __init__(self, *args):
        super().__init__(*args)
        self.Elements = ["Havoc", "Spectro"]
        self.Rover_Element = self.Elements[1]

    def do_perform(self):
        if self.Rover_Element == self.Elements[0]:
            self.click_liberation()
            if self.click_resonance()[0]:
                return self.switch_next_char()
            if self.is_forte_full():
                self.logger.info(f'forte_full, and liberation_available, heavy attack')
                self.wait_down()
                self.heavy_attack()
                self.sleep(0.4)
                if self.click_resonance()[0]:
                    return self.switch_next_char()
            self.click_echo()
            self.switch_next_char()
        elif self.Rover_Element == self.Elements[1]:
            if self.has_intro:
                self.wait_intro()
                self.n4(duration = 0.9)
            else:
                self.n4(duration = 0.6)
            forte_pass = False
            if self.click_liberation():
                self.click_echo()
                if not self.is_forte_full():
                    return self.switch_next_char()
                else:
                    forte_pass = True
            if forte_pass or self.is_forte_full():
                if self.click_resonance()[0]:
                    self.click_echo()
                    self.continues_normal_attack(1.4)
                    return self.switch_next_char()
            if self.click_resonance()[0]:
                self.click_echo()
            self.switch_next_char()

    def n4(self, duration = 0.9):
        self.heavy_attack()
        #self.continues_normal_attack(duration)
        self.sleep(0.4)
        self.continues_normal_attack(0.8)