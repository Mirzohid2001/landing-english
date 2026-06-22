"""Selenium E2E yordamchilari — Chrome ishlamasa testlar skip qilinadi."""
import unittest


def selenium_installed():
    try:
        import selenium  # noqa: F401
        return True
    except ImportError:
        return False


def create_chrome_driver(window_size='1280,900'):
    """
    Headless Chrome driver. Muvaffaqiyatsiz bo'lsa SkipTest — ERROR emas.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as exc:
        raise unittest.SkipTest(
            'selenium o\'rnatilmagan — pip install -r requirements-dev.txt'
        ) from exc

    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument(f'--window-size={window_size}')

    try:
        return webdriver.Chrome(options=opts)
    except Exception as exc:
        raise unittest.SkipTest(
            f'Chrome/Selenium ishga tushmadi: {exc}. '
            'Chrome o\'rnatilganini tekshiring yoki CI/sandbox tashqarisida ishga tushiring.'
        ) from exc


def quit_driver(driver):
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
