import pytest
import requests
from pytest_bdd import given, scenario, then, when

# The URL of an SLO Generator API running on Cloud Run with the latest version
API_CLOUD_RUN_URL: str = "https://slo-generator-ulho4vepfq-ew.a.run.app/"


class ApiHelper:
    responseCode = None


@pytest.fixture
def api():
    helper = ApiHelper()
    return helper


@scenario("../features/api.feature", "Calling the API endpoint with a GET")
def test_call_api_with_get(api):
    pass


@given("I am a public, unauthenticated user")
def public_unauthenticated_user():
    pass


@when("I call the API endpoint with a GET")
def call_api_endpoint_with_get(api: ApiHelper):
    response = requests.get(API_CLOUD_RUN_URL)
    api.responseCode = response.status_code


@then("The API is available")
def api_is_available(api: ApiHelper):
    assert api.responseCode == 200


@scenario(
    "../features/api.feature",
    "Calling the API endpoint with a POST and an SLO definition",
)
def test_call_api_with_post_and_slo_definition(api):
    pass


@when("I call the API endpoint with a POST and an SLO definition")
def call_api_endpoint_with_post_and_slo_definition(api: ApiHelper):
    with open("./samples/cloud_monitoring/slo_gae_app_availability.yaml", "rb") as f:
        payload = f.read()
        payload = payload.replace(b"${GAE_PROJECT_ID}", b"slo-generator-ci-a2b4")
        headers = {"content-type": "application/x-www-form-urlencoded"}
        response = requests.post(API_CLOUD_RUN_URL, data=payload, headers=headers)
        api.responseCode = response.status_code
        api.json = response.json()


@then("The API response is not empty")
def api_returns_some_data(api: ApiHelper):
    assert api.json


@then("The API response has the expected format")
def api_response_has_expected_format(api: ApiHelper):
    assert len(api.json) == 2 and all(
        key in api.json[0]
        for key in (
            "alert",
            "backend",
            "bad_events_count",
            "good_events_count",
            "events_count",
            "error_budget_burn_rate",
        )
    )


@then("The API response has the expected content")
def api_response_has_expected_content(api: ApiHelper):
    assert (
        api.json[0]["exporters"] == ["cloud_monitoring"]
        and api.json[0]["bad_events_count"] + api.json[0]["good_events_count"]
        == api.json[0]["events_count"]
    )
