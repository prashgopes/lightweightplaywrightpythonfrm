from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(self.base_url, wait_until="domcontentloaded")

    def login(self, username: str, password: str) -> None:
        self.page.get_by_role("link", name="Login", exact=True).first.click()
        self.page.get_by_label("Email ID / Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Login", exact=True).click()
        self.page.get_by_label("Password").wait_for(state="hidden", timeout=30_000)
