Feature: slo-generator API
    A REST-ful API to interact with the SLO Generator

    Scenario: Calling the API endpoint with a GET
        Given I am a public, unauthenticated user
        When I call the API endpoint with a GET
        Then The API is available

    Scenario: Calling the API endpoint with a POST and an SLO definition
        Given I am a public, unauthenticated user
        When I call the API endpoint with a POST and an SLO definition
        Then The API is available
        And The API response is not empty
        And The API response has the expected format
        And The API response has the expected content
