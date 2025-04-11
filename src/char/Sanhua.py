import time

from src.char.BaseChar import BaseChar


class Sanhua(BaseChar):
    def do_perform(self):
        sleep_time = 0.65
        self.sleep(0.02)
        self.task.mouse_down()
        self.sleep(0.1)
        start = time.time()
        if self.has_intro:
            sleep_time -= 0.1
            self.wait_intro(click=False, time_out=1.1)
        clicked_resonance, duration, _ = self.click_resonance(send_click=False)
        if clicked_resonance:
            sleep_time -= duration
            self.sleep(0.2)
        clicked_liberation = self.click_liberation(send_click=False)
        if clicked_liberation:
            sleep_time += 0.4
        sleep_time -= self.time_elapsed_accounting_for_freeze(start)
        self.logger.debug('Sanhua to_sleep {}'.format(sleep_time))
        self.sleep(sleep_time)
        self.task.mouse_up()
        if clicked_resonance or clicked_liberation:
            after_sleep = 1.1
        else:
            after_sleep = 0.3
        self.sleep(after_sleep)
        if self.get_current_con() >= 0.99:
            self.click_echo()
            self.sleep(0.05)
        self.switch_next_char()
