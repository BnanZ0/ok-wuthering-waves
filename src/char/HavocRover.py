from src.char.BaseChar import BaseChar


class HavocRover(BaseChar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Elements = ["Havoc", "Spectro"]
        self.Rover_Element = self.Elements[1]

    def do_perform(self):
        if self.Rover_Element == self.Elements[0]:
            if self.has_intro:
                if self.is_forte_full():
                    self.heavy_attack(1)
                else:
                    self.wait_intro(click=True)
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
            if not self.click_echo():
                self.click()
            self.switch_next_char()
        elif self.Rover_Element == self.Elements[1]:
            if self.has_intro:
                self.wait_intro()
            self.aftertune_combo()
            self.click_echo()
            if self.is_forte_full():
                self.check_combat()
                if self.click_resonance()[0]:
                    self.continues_normal_attack(1.4)
                    self.sleep(0.1)
                    if not self.liberation_available():
                        return self.switch_next_char()
            self.check_combat()
            if self.click_liberation():
                return self.switch_next_char()
            self.click_resonance()
            self.switch_next_char()

    def aftertune_combo(self):
        self.heavy_attack()
        self.sleep(0.4)
        self.continues_normal_attack(0.7)