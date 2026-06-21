"""
Admin question form E2E — question_admin.js ball/ko'rsatma xulq-atvori.

Requires: pip install -r requirements-dev.txt
Chrome/Chromium must be available (Selenium 4 manages the driver).
"""
import time
import unittest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from mock_tests.models import MockTest


def _chrome_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1400,1000')
    return webdriver.Chrome(options=opts)


@unittest.skipUnless(SELENIUM_AVAILABLE, 'selenium not installed (pip install -r requirements-dev.txt)')
class AdminQuestionPointsE2ETests(StaticLiveServerTestCase):
    """Admin inline savol formasida JS ball avto-yangilanishini tekshiradi."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = _chrome_driver()
        cls.driver.implicitly_wait(3)
        cls.wait = WebDriverWait(cls.driver, 15)

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admintest',
            email='admin@test.com',
            password='adminpass123',
        )

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def _admin_login(self):
        self.driver.delete_all_cookies()
        login_url = self.live_server_url + reverse('admin:login')
        self.driver.get(login_url)
        self.driver.find_element(By.NAME, 'username').send_keys('admintest')
        self.driver.find_element(By.NAME, 'password').send_keys('adminpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.wait.until(lambda d: 'login' not in d.current_url)

    def _open_mock_test_change(self, test):
        change_url = self.live_server_url + reverse('admin:mock_tests_mocktest_change', args=[test.pk])
        self.driver.get(change_url)
        self.wait.until(EC.presence_of_element_located((By.ID, 'questions-0')))

    def _first_question_row(self):
        row = self.wait.until(
            EC.presence_of_element_located((By.ID, 'questions-0'))
        )
        row_class = row.get_attribute('class') or ''
        if 'mock-inline-collapsed' in row_class:
            summary = row.find_element(By.CSS_SELECTOR, '.mock-row-summary')
            self.driver.execute_script('arguments[0].click();', summary)
            time.sleep(0.2)
        return row

    def _row_field(self, row, selector):
        return row.find_element(By.CSS_SELECTOR, selector)

    def _dispatch_input(self, element):
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
            element,
        )

    def test_admin_change_page_loads_question_admin_js(self):
        test = MockTest.objects.create(title='Admin JS load', test_type='reading', is_active=True)
        self._admin_login()
        self._open_mock_test_change(test)
        html = self.driver.page_source
        self.assertIn('question_admin.js', html)

    def test_points_field_updates_for_sentence_completion_brackets(self):
        test = MockTest.objects.create(title='Admin SC points', test_type='reading', is_active=True)
        self._admin_login()
        self._open_mock_test_change(test)

        row = self._first_question_row()
        type_select = self._row_field(row, 'select[name$="-question_type"]')
        self.driver.execute_script(
            "arguments[0].value = 'sentence_completion';"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            type_select,
        )
        time.sleep(0.4)

        qtext = self._row_field(row, 'textarea[name$="-question_text"]')
        qtext.clear()
        qtext.send_keys('First [7]. Second [8]. Third [9].')
        self._dispatch_input(qtext)
        time.sleep(0.4)

        points = self._row_field(row, 'input[name$="-points"]')
        self.assertEqual(points.get_attribute('value'), '3')
        self.assertIn('true', (points.get_attribute('readonly') or '').lower())

        hint = row.find_element(By.CSS_SELECTOR, '.mock-points-slot-hint')
        self.assertIn('Baholanadigan slotlar: 3', hint.text)

    def test_points_field_updates_for_summary_completion(self):
        test = MockTest.objects.create(title='Admin Summary Comp', test_type='reading', is_active=True)
        self._admin_login()
        self._open_mock_test_change(test)

        row = self._first_question_row()
        type_select = self._row_field(row, 'select[name$="-question_type"]')
        self.driver.execute_script(
            "arguments[0].value = 'summary_completion';"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            type_select,
        )
        time.sleep(0.4)

        qtext = self._row_field(row, 'textarea[name$="-question_text"]')
        qtext.clear()
        qtext.send_keys('Alpha [20]. Beta [21].')
        self._dispatch_input(qtext)
        time.sleep(0.4)

        points = self._row_field(row, 'input[name$="-points"]')
        self.assertEqual(points.get_attribute('value'), '2')
