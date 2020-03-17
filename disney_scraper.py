import json
import time

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Credentials
BASE_URL = "https://www.disneyplus.com/"
EMAIL = "dtest-1984@gmail.com"
PASSWORD = "Test!234"

# Environment Variables
HEADLESS = 0
IMPLICITLY_WAIT_STABLE = 10
IMPLICITLY_WAIT_NORMAL = 5
IMPLICITLY_WAIT_FAST = 1
RETRY_MAX = 5
RETRY_MIN = 1
ERROR_SLEEP = 0.3

# XPATH Constants
LOGIN_BTN_XPATH = "//button[@aria-label='Log in to your Disney Plus account.']"
CONTINUE_BTN_XPATH = "//button[@name='dssLoginSubmit']"
SLIDER_XPATH = "//div[@id='home-collection']"
SLIDER_ITEM_XPATH = "//div[@id='home-collection']/div"
SLIDER_NEXT_BTN_XPATH = "./div/div/button[2]"
NAME_XPATH = "./div/h4"
ITEM_NAME_XPATH = ".//a[contains(@class, 'basic-card skipToContentTarget')]"
ITEM_IMAGE_XPATH = ".//img"


class DisneyScraper:
    failed_tries = 0

    def __init__(self):
        self.base_url = BASE_URL
        self.driver = self.session()

    def session(self):
        chrome_options = webdriver.ChromeOptions()
        if HEADLESS == 1:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            chrome_options=chrome_options,
            service_log_path='/dev/null',
            executable_path='./bin/chromedriver'
        )

        driver.set_page_load_timeout(30)
        driver.implicitly_wait(IMPLICITLY_WAIT_NORMAL)
        driver.set_window_size(1360, 900)

        return driver

    def find_and_action(self, selector, by="xpath", can_fail=False,
                        action="click", before_sleep=None, after_sleep=None):
        if by == "xpath":
            by = By.XPATH
        elif by == "id":
            by = By.ID
        elif by == "partial_link_text":
            by = By.PARTIAL_LINK_TEXT
        else:
            raise Exception("Unknown search operator")
        try:
            wait_fast = IMPLICITLY_WAIT_FAST
            wait_stable = IMPLICITLY_WAIT_STABLE
            wait = WebDriverWait(
                self.driver, wait_fast if can_fail else wait_stable
            )
            element = wait.until(EC.element_to_be_clickable((by, selector)))
        except (TimeoutException, WebDriverException):
            self.log_error(can_fail, selector)
            return False
        if isinstance(element, list):
            element = element[0]
        if action == "check" and element.is_selected():
            return True
        self.click(element, can_fail, before_sleep, after_sleep)
        return True

    @staticmethod
    def log_error(can_fail, selector=None):
        if not can_fail:
            error_message = "Can't find element."
            error_message = error_message\
                if not selector else error_message + " Selector: " + selector
            print(error_message, exc_info=True)

    def click(self, element, can_fail=False, before_sleep=None,
              after_sleep=None):
        try:
            if before_sleep:
                time.sleep(float(before_sleep))
            element.click()
            if after_sleep:
                time.sleep(float(after_sleep))
        except WebDriverException:
            self.failed_tries += 1
            retry_min = RETRY_MIN
            retry_max = RETRY_MAX
            max_fails = retry_min if can_fail else retry_max
            if self.failed_tries >= max_fails:
                self.log_error(can_fail)
                self.failed_tries = 0
                return
            self.click(element, can_fail, before_sleep, after_sleep)
        self.failed_tries = 0

    def clear_and_send_keys(self, selector, value, by="xpath",
                            start_with_clear=True, end_with_enter=True):
        element = None
        if by == "operator":
            element = selector
        else:
            try:
                element = self.get_element(by, selector)
            except WebDriverException:
                self.failed_tries += 1
                if self.failed_tries >= RETRY_MAX:
                    self.log_error(False, selector)
                    self.failed_tries = 0
                    return
                self.clear_and_send_keys(selector, value, by,
                                         start_with_clear, end_with_enter)
        self.failed_tries = 0
        self.send_keys(element, value, start_with_clear, end_with_enter)

    def send_keys(self, element, value, start_with_clear, end_with_enter):
        count = 0
        while not element.is_displayed():
            time.sleep(ERROR_SLEEP)
            count += 1
            if count > RETRY_MAX:
                print("error", "Can't send a keys for the element")
        try:
            if start_with_clear:
                element.clear()
            element.send_keys(value)
            if end_with_enter:
                element.send_keys(Keys.ENTER)
        except WebDriverException:
            self.send_keys(element, value, start_with_clear, end_with_enter)

    def get_element(self, by, selector, check_exists=False):
        try:
            if by == "xpath":
                element = self.driver.find_element_by_xpath(selector)
            elif by == "id":
                element = self.driver.find_element_by_id(selector)
            elif by == "partial_link_text":
                element =\
                    self.driver.find_element_by_partial_link_text(selector)
            else:
                raise Exception("Unknown search operator")
        except NoSuchElementException as e:
            if check_exists:
                return None
            else:
                raise e

        return element

    def is_element_displayed(self, selector, by="xpath"):
        try:
            element = self.get_element(by, selector)
            return element.is_displayed()
        except WebDriverException:
            pass

        return False

    def is_failed(self):
        time.sleep(ERROR_SLEEP)
        self.failed_tries += 1
        if self.failed_tries > RETRY_MAX:
            return True
        return False

    def wait_for_element(self, selector, element_status="show"):
        is_failed = False

        if element_status == "show":
            while not self.is_element_displayed(selector):
                if self.is_failed():
                    is_failed = True
                    break
        elif element_status == "locate":
            wait_stable = IMPLICITLY_WAIT_STABLE
            wait = WebDriverWait(self.driver, wait_stable)

            try:
                wait.until(EC.presence_of_element_located(("xpath", selector)))
            except TimeoutException:
                self.log_error(True, selector)
                is_failed = True

        self.failed_tries = 0

        return is_failed

    def make_element_visible(self, element):
        self.driver.execute_script("return arguments[0].scrollIntoView();",
                                   element)

    def make_element_click(self, element):
        self.driver.execute_script("arguments[0].click();", element)

    def login(self):
        try:
            self.driver.get(self.base_url)
            time.sleep(IMPLICITLY_WAIT_NORMAL)
        except TimeoutException:
            print('Connection Timeout Problem...')
            return False
        try:
            self.find_and_action(LOGIN_BTN_XPATH,
                                 after_sleep=IMPLICITLY_WAIT_FAST)
            self.clear_and_send_keys("email", EMAIL, "id", False, True)
            self.clear_and_send_keys("password", PASSWORD, "id", False, True)
            time.sleep(IMPLICITLY_WAIT_NORMAL)
            is_logged_in =\
                not self.wait_for_element("//div[@id='home-collection']")
        except NoSuchElementException:
            return False
        return is_logged_in

    def scrape_movies_series(self):
        if self.wait_for_element(SLIDER_XPATH):
            return None

        output_data = {
            "sections": []
        }

        slider_counts =\
            len(self.driver.find_elements_by_xpath(SLIDER_ITEM_XPATH))

        for i in range(2, slider_counts):

            # get section name
            name =\
                self.driver.find_elements_by_xpath(
                    SLIDER_ITEM_XPATH
                )[i].find_element_by_xpath(NAME_XPATH).text

            print(f"[INFO]: Processing {i - 2}th section: {name} ")

            # get the item counts
            item_counts =\
                len(
                    self.driver.find_elements_by_xpath(
                        SLIDER_ITEM_XPATH
                    )[i].find_elements_by_xpath(ITEM_NAME_XPATH)
                )

            items = []

            for j in range(0, item_counts):
                try:
                    # get each item
                    item = self.driver.find_elements_by_xpath(
                        SLIDER_ITEM_XPATH
                    )[i].find_elements_by_xpath(ITEM_NAME_XPATH)[j]

                    # get movie name
                    item_name = item.find_elements_by_xpath(
                        "./div")[0].get_attribute('alt')
                    print(f"[INFO]: Processing {j}th item: {item_name} ")

                    # get movie image link
                    item_image = item.find_elements_by_xpath(
                        ITEM_IMAGE_XPATH)[0].get_attribute('src')

                    # Click the detail card for getting detail link
                    self.make_element_click(item)
                    item_url = self.driver.current_url
                    self.driver.back()

                    # save the item data
                    items.append({
                        "name": item_name,
                        "image": item_image,
                        "url": item_url
                    })
                except Exception:
                    pass

                # click the scroll right button
                if j > 0 and j % 5 == 0:
                    try:
                        slider_next_btn =\
                            self.driver.find_elements_by_xpath(
                                SLIDER_ITEM_XPATH)[i].find_elements_by_xpath(
                                    SLIDER_NEXT_BTN_XPATH)[0]

                        if slider_next_btn:
                            self.make_element_click(slider_next_btn)
                    except NoSuchElementException:
                        pass

            # add the result
            output_data["sections"].append({
                "name": name,
                "items": items
            })

            # scroll to the current slider in order to
            # load the images from below sliders
            self.make_element_visible(
                self.driver.find_elements_by_xpath(SLIDER_ITEM_XPATH)[i]
            )

        # save the result to the file
        with open("output.json", "w") as f:
            json.dump(output_data, f, indent=True)

    def run_scraper(self):
        if not self.login():
            return None
        self.scrape_movies_series()
        return None


if __name__ == '__main__':
    scraper = DisneyScraper()
    scraper.run_scraper()
    scraper.driver.quit()
