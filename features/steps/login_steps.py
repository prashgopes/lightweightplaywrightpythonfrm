from behave import given, then, when

from pages.login_page import LoginPage


@given("the Naukri home page is open")
def open_home_page(context) -> None:
    context.login_page.open()


@when("I log in with my configured credentials")
def log_in(context) -> None:
    context.login_page.login(context.credentials["username"], context.credentials["password"])


@then("I should be logged in successfully")
def verify_logged_in(context) -> None:
    assert not context.page.get_by_label("Password").is_visible(), (
        "The Naukri login form is still visible; authentication may have failed."
    )
