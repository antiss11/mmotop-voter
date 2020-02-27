from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import datetime
from pytz import timezone
import time
from dateutil import parser


def mmotop_time():
    return datetime.datetime.now(timezone("Europe/Vilnius"))


def can_voted_time(mmotop_timer):
    delta = datetime.timedelta(hours=mmotop_timer.hour, minutes=mmotop_timer.minute,
                               seconds=mmotop_timer.second)
    now = datetime.datetime.now()
    can_time = now + delta

    def helper():
        return datetime.datetime.now() >= can_time
    return helper()


class Browser(webdriver.Chrome):

    vote_button_xpath = "//a[@class='btn btn-danger icon-thumbs-up']"

    def __init__(self):
        webdriver.Chrome.__init__(self)

    def login(self, vk_login, vk_password):
        self._waiting(xpath=Browser.vote_button_xpath, delay=30)
        self.find_element_by_xpath(Browser.vote_button_xpath).click()
        vk_login_button_xpath = "//a[@href='/users/auth/vkontakte']"
        time.sleep(2)
        self._waiting(xpath=vk_login_button_xpath, type="element_to_be_clickable")
        self.find_element_by_xpath(vk_login_button_xpath).click()
        self._waiting(xpath="//input[@name='email']")
        self.find_element_by_xpath("//input[@name='email']").send_keys(vk_login)
        self.find_element_by_xpath("//input[@name='pass']").send_keys(vk_password)
        self.find_element_by_xpath("//button[@id='install_allow']").click()

    def _do_slide(self):
        slider = self.find_element_by_xpath("//div[@class='Slider ui-draggable']")
        slider_width = slider.size["width"]
        field_width = self.find_element_by_xpath("//div[@class='bgSlider']").size["width"]
        offset = field_width - slider_width
        actions = ActionChains(self)
        actions.drag_and_drop_by_offset(slider, offset, 0).perform()

    def is_voted(self):
        try:
            self.find_element_by_xpath("//span[@class='countdown_row countdown_amount']")
            return True
        except NoSuchElementException:
            return False

    def get_timer(self):
        self._waiting(xpath="//span[@class='countdown_row countdown_amount']",
                      type="element_to_be_clickable")
        return self.find_element_by_xpath("//span[@class='countdown_row countdown_amount']").text

    def _waiting(self, xpath=None, id=None, elem_class=None, link_text=None,
                type="default", delay=None):
        delay = delay or 20

        if type == "default":
            if xpath:
                WebDriverWait(self, delay).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
            elif id:
                WebDriverWait(self, delay).until(
                    EC.presence_of_element_located((By.ID, id)))
            elif elem_class:
                WebDriverWait(self, delay).until(
                    EC.presence_of_element_located((By.CLASS_NAME, elem_class)))
            elif link_text:
                WebDriverWait(self, delay).until(
                    EC.presence_of_element_located((By.LINK_TEXT, link_text)))

        elif type == "element_to_be_clickable":
            if xpath:
                WebDriverWait(self, delay).until(
                    EC.element_to_be_clickable((By.XPATH, xpath)))
            elif id:
                WebDriverWait(self, delay).until(
                    EC.element_to_be_clickable((By.ID, id)))
            elif elem_class:
                WebDriverWait(self, delay).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, elem_class)))
            elif link_text:
                WebDriverWait(self, delay).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, link_text)))

    def _is_404(self):
        try:
            self.find_element_by_xpath("//div[@class='body error-404']")
            return True
        except NoSuchElementException:
            return False

    def choice_world(self, n):
        time.sleep(2)
        worlds = self.find_elements_by_xpath("//tr[@style='cursor: pointer;']")
        n = n-1
        worlds[n].click()

    def input_name(self, name):
        self._waiting(xpath="//input[@type='text']")
        self.execute_script(f"$('#charname input').val('{name}');")

    def confirm(self):
        self.find_element_by_xpath("//input[@id='check_vote_form']").click()

    def get_page_with_timer(self, url):
        self.get(url)
        self.find_element_by_xpath(Browser.vote_button_xpath).click()
        return self.get_timer()

    def main(self, vk_login, vk_password, url, name, world_n, log):
        self.get(url)
        log("Перешли на сайт mmotop")
        self.login(vk_login, vk_password)
        log("Залогинились")
        if self.is_voted():
            timer = self.get_timer()
            log(f"Следующий голос через {timer}")
        else:
            self._do_slide()
            self.input_name(name)
            self.choice_world(world_n)
            self.confirm()
            log("Проголосовали")


def main(vk_login, vk_password, url, name, world_n, once, log):
    while True:
        browser = Browser()
        browser.main(vk_login=vk_login, vk_password=vk_password, url=url, name=name,
                     world_n=world_n, log=log)
        if not once:
            timer = parser.parse(browser.get_page_with_timer(url))
        browser.quit()
        if once:
            log("Программа завершила работу")
            break
        else:
            log("Ждем...")
            while not can_voted_time(timer):
                time.sleep(300)