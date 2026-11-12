Feature: Naukri account login
  As a job seeker
  I want to log in to Naukri
  So that I can access my account

  @smoke
  Scenario: Log in with valid credentials
    Given the Naukri home page is open
    When I log in with my configured credentials
    Then I should be logged in successfully
