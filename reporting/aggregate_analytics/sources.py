import os

import httpx

from reporting.aggregate_analytics.database import EventRow, count_rows, monthly_count_rows
from reporting.aggregate_analytics.measures import Count, Source

# Keyed by (organisation_id as string or None, "YYYY-MM").
MonthlyCounts = dict[tuple[str | None, str], int]


def _plausible_query(body: dict[str, object]) -> list[dict[str, list[object]]]:
    base_url = os.environ["PLAUSIBLE_BASE_URL"].rstrip("/")
    bearer_token = os.environ["PLAUSIBLE_API_KEY"]
    site_id = os.environ["PLAUSIBLE_SITE_ID"]

    response = httpx.post(
        f"{base_url}/api/v2/query",
        headers={"Authorization": f"Bearer {bearer_token}"},
        json={"site_id": site_id, "metrics": ["events"], **body},
        timeout=30,
    )
    if response.is_error:
        msg = f"Plausible returned {response.status_code}: {response.text} (query: {body})"
        raise RuntimeError(msg)
    results: list[dict[str, list[object]]] = response.json()["results"]
    return results


def plausible_event_count(event: str, start: str, end: str) -> int:
    """Count a Plausible custom event between two inclusive YYYY-MM-DD dates."""
    results = _plausible_query({"date_range": [start, end], "filters": [["is", "event:name", [event]]]})
    return int(results[0]["metrics"][0]) if results else 0  # type: ignore[call-overload]


def plausible_monthly_counts(events: tuple[str, ...], start: str, end: str, *, by_organisation: bool) -> MonthlyCounts:
    """Count Plausible events (summed) per calendar month, optionally split by the organisation_id property.

    Months follow the Plausible site's timezone. Events without an organisation_id are keyed to None.
    """
    dimensions = ["time:month", *(["event:props:organisation_id"] if by_organisation else [])]
    results = _plausible_query(
        {
            "date_range": [start, end],
            "dimensions": dimensions,
            "filters": [["is", "event:name", list(events)]],
            "pagination": {"limit": 10000},
        }
    )

    counts: MonthlyCounts = {}
    for result in results:
        month = str(result["dimensions"][0])[:7]
        organisation = str(result["dimensions"][1]) if by_organisation else None
        key = (organisation.lower() if organisation and organisation != "(none)" else None, month)
        counts[key] = counts.get(key, 0) + int(result["metrics"][0])  # type: ignore[call-overload]
    return counts


def count_event(rows: list[EventRow], count: Count, start: str, end: str) -> int:
    """Postgres counts come from the already-fetched `rows`; Plausible counts are queried."""
    if count.source == "plausible":
        return plausible_event_count(count.event, start, end)
    return count_rows(rows, count.event, count.recording_source)


def monthly_counts(
    rows: list[EventRow],
    source: Source,
    events: tuple[str, ...],
    start: str,
    end: str,
    *,
    by_organisation: bool,
) -> MonthlyCounts:
    if source == "plausible":
        return plausible_monthly_counts(events, start, end, by_organisation=by_organisation)
    return monthly_count_rows(rows, events, by_organisation=by_organisation)
