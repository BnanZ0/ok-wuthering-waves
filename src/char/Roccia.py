import time

from src.char.BaseChar import BaseChar, Priority


class Roccia(BaseChar):

    def __init__(self, *args):
        super().__init__(*args)
        self.plunge_count = 0

    # def do_perform(self):
    #     self.wait_intro(time_out=1.2, click=True)
    #     if self.get_plunge_count() > 0:
    #         self.plunge()
    #         return self.switch_next_char()
    #     if self.is_forte_full() and self.resonance_available():
    #         self.click_liberation()
    #     if self.click_resonance()[0]:
    #         plunge_count = self.task.wait_until(self.get_plunge_count, time_out=2, post_action=self.click_with_interval, wait_until_before_delay=0,
    #                            wait_until_check_delay=0)
    #         self.logger.debug('wait plunge count: {}'.format(plunge_count))
    #         # if plunge_count == 3:
    #         #     self.plunge()
    #         return self.switch_next_char()
    #     self.click()
    #     post_action = self.use_t_action if self.is_con_full() else None
    #     self.switch_next_char(post_action=post_action)

    def do_perform(self):
        self.wait_intro(time_out=1.4, click=True)
        self.plunge_count = self.get_plunge_count()
        if self.plunge_count > 0:
            self.plunge_count = 0
            # self.()
            return self.switch_next_char()
        # if not self.is_forte_full():
        #     self.heavy_attack(1.5)
        #     return super().switch_next_char()
        if self.is_forte_full() and self.resonance_available() and self.liberation_available():
            self.click_liberation()
        if self.click_resonance()[0]:
            self.plunge_count = 2
            return self.switch_next_char()
        self.plunge_count = 0
        self.switch_next_char()

    def switch_next_char(self, *args):
        # self.click(interval=0.2)
        # while time.time() - self.last_perform < 1.1:
        #     self.click(interval=0.2)
        self.click()
        # if self.plunge_count == 0:
        #     self.plunge_count = self.get_plunge_count()
        # self.logger.debug('wait plunge count: {}'.format(self.plunge_count))
        # post_action = self.use_t_action if self.is_con_full() else None
        return super().switch_next_char(*args)

    def use_t_action(self):
        self.task.send_key('t')
        self.sleep(0.01)

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if has_intro and self.plunge_count > 0:
            return Priority.MIN
        if self.plunge_count > 0 or has_intro:
            self.logger.info(
                f'switch priority max because plunge count is {self.plunge_count}')
            return Priority.MAX - 1
        else:
            return super().do_get_switch_priority(current_char, has_intro, target_low_con)

    def get_plunge_count(self):
        count = 0
        if self.is_color_ok('box_forte_1'):
            count += 1
        if self.is_color_ok('box_forte_2'):
            count += 1
        if self.is_color_ok('box_forte_3'):
            count += 1
        return count

    def is_color_ok(self, box):
        purple_percent = self.task.calculate_color_percentage(forte_purple_color, self.task.get_box_by_name(box))
        self.logger.debug(f'purple percent: {box} {purple_percent}')
        if purple_percent > 0.15:
            return True

    def plunge(self, starting_count=3):
        start = time.time()
        while self.is_forte_full() and time.time() - start < 4:
            # plunge_count = self.get_plunge_count()
            # if plunge_count > 0:
            #     starting_count = plunge_count - 1
            # elif  starting_count > 1:
            self.click(interval=0.1)
            if self.get_plunge_count() == 1:
                break
        self.plunge_count = 0
        self.logger.debug(f'plunge ended after: {time.time() - start} {self.get_plunge_count()}  {self.is_forte_full()}')
        return True

    def c6_continues_plunge(self):
        start = time.time()
        # has_charge = self.is_forte_full()
        while time.time() - start < 11:
            self.click(interval=0.1)
        return True


forte_purple_color = {
    'r': (70, 105),  # Red range
    'g': (30, 65),  # Green range
    'b': (160, 235)  # Blue range
}