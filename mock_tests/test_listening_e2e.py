"""
Listening flow E2E tests (Selenium + Django live server).

Requires: pip install -r requirements-dev.txt
Chrome/Chromium must be available (Selenium 4 manages the driver).
"""
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
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

from mock_tests.tests import MockTestFixturesMixin


def _chrome_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1280,900')
    return webdriver.Chrome(options=opts)


@unittest.skipUnless(SELENIUM_AVAILABLE, 'selenium not installed (pip install -r requirements-dev.txt)')
class ListeningFlowE2ETests(StaticLiveServerTestCase, MockTestFixturesMixin):
    """Brauzer orqali listening test oqimini tekshiradi."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = _chrome_driver()
        cls.driver.implicitly_wait(3)
        cls.wait = WebDriverWait(cls.driver, 12)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.test = self._create_listening_test_with_audio()
        self.take_path = reverse('mock_tests:test_take', kwargs={'pk': self.test.pk})
        self.take_url = self.live_server_url + self.take_path

    @classmethod
    def _create_listening_test_with_audio(cls):
        test = cls._create_listening_test()
        test.audio_file.save(
            'e2e-demo.mp3',
            SimpleUploadedFile('e2e-demo.mp3', b'fake-audio-bytes', content_type='audio/mpeg'),
        )
        return test

    def _open_take_page(self, clear_onboarding=True):
        if clear_onboarding:
            self.driver.get(self.live_server_url + '/')
            self.driver.execute_script("localStorage.removeItem('mock_onboarding_v1_done');")
        self.driver.get(self.take_url)

    def _dismiss_onboarding_if_visible(self):
        try:
            overlay = self.driver.find_element(By.ID, 'mock-onboarding')
            if overlay.is_displayed():
                self._click_js(self.driver.find_element(By.ID, 'mock-onboarding-skip'))
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.mock-onboarding.is-open')))
        except Exception:
            pass

    def _dismiss_ui_overlays(self):
        """Tip bar va boshqa qatlam elementlarini yopish."""
        self.driver.execute_script(
            """
            document.getElementById('mock-tip-bar')?.classList.add('is-dismissed');
            const ob = document.getElementById('mock-onboarding');
            if (ob && !ob.hidden) {
                ob.hidden = true;
                ob.classList.remove('is-open');
            }
            """
        )

    def _click_js(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", element)
        self.driver.execute_script("arguments[0].click();", element)

    def test_onboarding_shows_and_can_skip(self):
        self._open_take_page(clear_onboarding=True)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.mock-onboarding.is-open')))
        self.wait.until(lambda d: d.find_element(By.ID, 'mock-onboarding-title').text.strip())
        title = self.driver.find_element(By.ID, 'mock-onboarding-title')
        self.assertTrue(title.text.strip())
        self.driver.find_element(By.ID, 'mock-onboarding-skip').click()
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.mock-onboarding.is-open')))

    def test_answered_count_updates_when_typing(self):
        self._open_take_page()
        self._dismiss_onboarding_if_visible()
        self._dismiss_ui_overlays()
        blank = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.mock-inline-input[data-blank="1"]'))
        )
        blank.clear()
        blank.send_keys('anna')
        self.wait.until(lambda d: d.find_element(By.ID, 'answered-count').text.strip() == '1')

    def test_audio_progress_reflects_seek(self):
        self._open_take_page()
        self._dismiss_onboarding_if_visible()
        self._dismiss_ui_overlays()
        self.wait.until(EC.presence_of_element_located((By.ID, 'audio-progress-track')))
        pct = self.driver.execute_script(
            """
            const audio = document.getElementById('exam-audio');
            const track = document.getElementById('audio-progress-track');
            const fill = document.getElementById('audio-progress-fill');
            if (!audio || !track || !fill) return 0;
            try {
                Object.defineProperty(audio, 'duration', { configurable: true, value: 100 });
            } catch (e) {}
            const rect = track.getBoundingClientRect();
            const x = rect.left + rect.width * 0.5;
            track.dispatchEvent(new MouseEvent('click', {
                clientX: x, clientY: rect.top + rect.height / 2, bubbles: true
            }));
            return parseFloat(fill.style.width) || 0;
            """
        )
        self.assertGreater(pct, 40)

    def test_submit_modal_shows_answer_stats(self):
        self._open_take_page()
        self._dismiss_onboarding_if_visible()
        self._dismiss_ui_overlays()
        blank = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.mock-inline-input[data-blank="1"]'))
        )
        blank.clear()
        blank.send_keys('anna')
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", blank
        )
        self.wait.until(lambda d: d.find_element(By.ID, 'answered-count').text.strip() in ('1', '2'))
        self._click_js(self.driver.find_element(By.ID, 'finish-test-btn'))
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#submit-modal.is-open')))
        self.wait.until(
            lambda d: d.find_element(By.ID, 'submit-answered').text.strip() in ('1', '2')
        )
        answered = self.driver.find_element(By.ID, 'submit-answered')
        self.assertIn(answered.text.strip(), ('1', '2'))
        self._click_js(self.driver.find_element(By.CSS_SELECTOR, '[data-close-submit]'))
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '#submit-modal.is-open')))

    def test_listening_full_flow_finish_to_result(self):
        self._open_take_page()
        self._dismiss_onboarding_if_visible()
        self._dismiss_ui_overlays()

        notes_q = self.test.questions.get(question_type='notes_completion')
        mcq_q = self.test.questions.get(question_type='mcq')

        self.driver.find_element(
            By.CSS_SELECTOR, f'input.mock-inline-input[data-question-id="{notes_q.pk}"][data-blank="1"]'
        ).send_keys('anna')
        self.driver.find_element(
            By.CSS_SELECTOR, f'input.mock-inline-input[data-question-id="{notes_q.pk}"][data-blank="2"]'
        ).send_keys('london')
        radio = self.driver.find_element(
            By.CSS_SELECTOR, f'input[type="radio"][data-question-id="{mcq_q.pk}"][value="b"]'
        )
        self._click_js(radio)

        self.wait.until(lambda d: d.find_element(By.ID, 'answered-count').text.strip() == '3')

        self._click_js(self.driver.find_element(By.ID, 'finish-test-btn'))
        self._click_js(self.wait.until(EC.element_to_be_clickable((By.ID, 'confirm-submit-btn'))))

        self.wait.until(EC.url_contains('/result/'))
        self.assertIn('Test natijasi', self.driver.page_source)
        self.assertIn('mock-result-card', self.driver.page_source)


@unittest.skipUnless(SELENIUM_AVAILABLE, 'selenium not installed (pip install -r requirements-dev.txt)')
class McqExtendedE2ETests(StaticLiveServerTestCase, MockTestFixturesMixin):
    """8 variantli va 2 javobli MCQ brauzer oqimi."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = _chrome_driver()
        cls.driver.implicitly_wait(3)
        cls.wait = WebDriverWait(cls.driver, 12)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.test = self._create_listening_mcq_extended_test()
        self.single_q = self.test.questions.get(order=1)
        self.multi_q = self.test.questions.get(order=2)
        self.take_url = self.live_server_url + reverse(
            'mock_tests:test_take', kwargs={'pk': self.test.pk}
        )

    def _open_take_page(self):
        self.driver.get(self.live_server_url + '/')
        self.driver.execute_script("localStorage.removeItem('mock_onboarding_v1_done');")
        self.driver.get(self.take_url)
        self._dismiss_onboarding_if_visible()
        self._dismiss_ui_overlays()

    def _dismiss_onboarding_if_visible(self):
        try:
            overlay = self.driver.find_element(By.ID, 'mock-onboarding')
            if overlay.is_displayed():
                self.driver.execute_script(
                    "arguments[0].click();",
                    self.driver.find_element(By.ID, 'mock-onboarding-skip'),
                )
                self.wait.until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, '.mock-onboarding.is-open'))
                )
        except Exception:
            pass

    def _dismiss_ui_overlays(self):
        self.driver.execute_script(
            """
            document.getElementById('mock-tip-bar')?.classList.add('is-dismissed');
            const ob = document.getElementById('mock-onboarding');
            if (ob && !ob.hidden) {
                ob.hidden = true;
                ob.classList.remove('is-open');
            }
            """
        )

    def _click_js(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'nearest'});", element
        )
        self.driver.execute_script("arguments[0].click();", element)

    def test_mcq_eight_options_rendered(self):
        self._open_take_page()
        radios = self.driver.find_elements(
            By.CSS_SELECTOR,
            f'input[type="radio"][data-question-id="{self.single_q.pk}"]',
        )
        self.assertEqual(len(radios), 8)
        values = sorted(r.get_attribute('value') for r in radios)
        self.assertEqual(values, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

    def test_mcq_eight_option_select_updates_count(self):
        self._open_take_page()
        radio = self.wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                f'input[type="radio"][data-question-id="{self.single_q.pk}"][value="b"]',
            ))
        )
        self._click_js(radio)
        self.wait.until(
            lambda d: d.find_element(By.ID, 'answered-count').text.strip() == '1'
        )

    def test_mcq_two_answer_checkboxes_and_hint(self):
        self._open_take_page()
        group = self.wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                f'.mock-options--multi[data-question-id="{self.multi_q.pk}"]',
            ))
        )
        self.assertIn('2 ta javob tanlang', group.text)
        checks = group.find_elements(By.CSS_SELECTOR, 'input.mock-mcq-check')
        self.assertEqual(len(checks), 5)

    def test_mcq_two_answer_select_updates_count(self):
        self._open_take_page()
        for letter in ('a', 'c'):
            cb = self.driver.find_element(
                By.CSS_SELECTOR,
                f'input.mock-mcq-check[data-question-id="{self.multi_q.pk}"][value="{letter}"]',
            )
            self._click_js(cb)
        self.wait.until(
            lambda d: d.find_element(By.ID, 'answered-count').text.strip() == '1'
        )

    def test_mcq_two_answer_max_three_prevented(self):
        self._open_take_page()
        group = self.wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                f'.mock-options--multi[data-question-id="{self.multi_q.pk}"]',
            ))
        )
        for letter in ('a', 'c', 'b'):
            cb = group.find_element(
                By.CSS_SELECTOR, f'input.mock-mcq-check[value="{letter}"]'
            )
            self._click_js(cb)
        checked = group.find_elements(By.CSS_SELECTOR, 'input.mock-mcq-check:checked')
        self.assertEqual(len(checked), 2)
        checked_vals = sorted(cb.get_attribute('value') for cb in checked)
        self.assertEqual(checked_vals, ['a', 'c'])

    def test_mcq_extended_full_flow_finish_to_result(self):
        self._open_take_page()
        self._click_js(self.driver.find_element(
            By.CSS_SELECTOR,
            f'input[type="radio"][data-question-id="{self.single_q.pk}"][value="b"]',
        ))
        for letter in ('a', 'c'):
            self._click_js(self.driver.find_element(
                By.CSS_SELECTOR,
                f'input.mock-mcq-check[data-question-id="{self.multi_q.pk}"][value="{letter}"]',
            ))
        self.wait.until(
            lambda d: d.find_element(By.ID, 'answered-count').text.strip() == '2'
        )
        self._click_js(self.driver.find_element(By.ID, 'finish-test-btn'))
        self._click_js(self.wait.until(EC.element_to_be_clickable((By.ID, 'confirm-submit-btn'))))
        self.wait.until(EC.url_contains('/result/'))
        self.assertIn('Test natijasi', self.driver.page_source)
