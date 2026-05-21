from pprint import pprint

from ucp_nine.models import ShopperRequest
from ucp_nine.orchestrator import UcpJourneyOrchestrator


def main() -> None:
    request = ShopperRequest(
        shopper_id="shopper_naresh",
        prompt="Find me coffee under 40 dollars and ship it to Cincinnati",
        destination_zip="45202",
        max_budget="40.00",
        human_approved_checkout=True,
    )
    result = UcpJourneyOrchestrator().run(request)
    pprint(result.model_dump(mode="json"))


if __name__ == "__main__":
    main()

