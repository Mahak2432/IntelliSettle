from datetime import date, datetime

import pytest

from claims_api.domain.models import CheckStatus, ClaimStatus, GeoPoint, Peril, Signal
from claims_api.products.crop import CropParametricProduct, CropTermSheet, Slab, slab_percent
from tests import factories as f

product = CropParametricProduct()


def statuses(ctx) -> dict[str, CheckStatus]:
    return {c.code: c.status for c in product.hard_checks(ctx)}


def test_clean_claim_passes_every_check():
    assert set(statuses(f.context()).values()) == {CheckStatus.PASS}


def test_peril_not_on_policy_fails():
    ctx = f.context(policy=f.policy(perils=[Peril.FLOOD]), claim=f.claim(peril=Peril.HAILSTORM))
    assert statuses(ctx)["peril_covered"] == CheckStatus.FAIL


def test_loss_outside_cover_period_fails():
    ctx = f.context(
        claim=f.claim(loss_date=date(2024, 12, 5), submitted_at=datetime(2024, 12, 6, tzinfo=f.IST))
    )
    assert statuses(ctx)["policy_active"] == CheckStatus.FAIL


@pytest.mark.parametrize(("submitted_day", "expected"), [(29, "pass"), (2, "pass"), (3, "fail")])
def test_reporting_window_is_72_hours(submitted_day, expected):
    month = 9 if submitted_day == 29 else 10
    ctx = f.context(claim=f.claim(submitted_at=datetime(2024, month, submitted_day, 18, 0, tzinfo=f.IST)))
    assert statuses(ctx)["reported_in_time"] == CheckStatus(expected)


def test_loss_date_in_future_fails_reporting_check():
    ctx = f.context(claim=f.claim(loss_date=date(2024, 10, 5)))
    assert statuses(ctx)["reported_in_time"] == CheckStatus.FAIL


def test_land_record_missing_owner_mismatch_and_inflated_area_fail():
    assert statuses(f.context(land_record=None))["land_record_match"] == CheckStatus.FAIL
    other_owner = f.land_record(owner_farmer_id="F-999")
    assert statuses(f.context(land_record=other_owner))["land_record_match"] == CheckStatus.FAIL
    small = f.land_record(area_ha=0.4)
    assert statuses(f.context(land_record=small))["land_record_match"] == CheckStatus.FAIL


def test_crop_survey_mismatch_fails_and_missing_entry_is_unknown():
    assert statuses(f.context(sowing_record=f.sowing_record(crop="maize")))["crop_sown_match"] == "fail"
    assert statuses(f.context(sowing_record=None))["crop_sown_match"] == CheckStatus.UNKNOWN


def test_photo_far_from_plot_fails_and_missing_gps_is_unknown():
    far = f.photo(device_location=GeoPoint(lat=f.PLOT_LOCATION.lat + 0.05, lon=f.PLOT_LOCATION.lon))
    assert statuses(f.context(claim=f.claim(photos=[far])))["photo_at_plot"] == CheckStatus.FAIL
    blind = f.photo(device_location=None)
    assert statuses(f.context(claim=f.claim(photos=[blind])))["photo_at_plot"] == CheckStatus.UNKNOWN


def test_exif_location_is_preferred_over_device_location():
    p = f.photo(
        exif_location=GeoPoint(lat=f.PLOT_LOCATION.lat + 0.2, lon=f.PLOT_LOCATION.lon),
        device_location=f.PLOT_LOCATION,
    )
    assert statuses(f.context(claim=f.claim(photos=[p])))["photo_at_plot"] == CheckStatus.FAIL


def test_photo_taken_before_the_event_fails():
    old = f.photo(device_captured_at=datetime(2024, 8, 1, 12, 0, tzinfo=f.IST))
    assert statuses(f.context(claim=f.claim(photos=[old])))["photo_after_loss"] == CheckStatus.FAIL


def test_overlapping_claim_on_same_policy_fails_unless_rejected():
    earlier = f.claim(loss_date=date(2024, 9, 27))
    assert statuses(f.context(other_claims=[earlier]))["no_duplicate_claim"] == CheckStatus.FAIL
    rejected = f.claim(loss_date=date(2024, 9, 27), status=ClaimStatus.REJECTED)
    assert statuses(f.context(other_claims=[rejected]))["no_duplicate_claim"] == CheckStatus.PASS


def test_reused_photo_is_caught_by_exact_and_perceptual_match():
    original = f.photo(phash="ffd8000000000000")
    copy = f.photo(sha256=original.sha256)
    near = f.photo(phash="ffd8000000000001")
    other_claim = f.claim(farmer_id="F-777", policy_no="POL-777", photos=[original])
    for p in (copy, near):
        ctx = f.context(claim=f.claim(photos=[p]), other_claims=[other_claim])
        assert statuses(ctx)["no_reused_photo"] == CheckStatus.FAIL


def test_documents_low_confidence_is_unknown_and_mismatch_fails():
    blurry = f.documents(land_record=f.extraction("land_record", confidence=0.6))
    assert statuses(f.context(claim=f.claim(documents=blurry)))["documents_match_records"] == "unknown"
    wrong_bank = f.documents(bank_passbook=f.extraction("bank_passbook", ifsc="HDFC0009999"))
    assert statuses(f.context(claim=f.claim(documents=wrong_bank)))["documents_match_records"] == "fail"
    assert statuses(f.context(claim=f.claim(documents=[])))["documents_match_records"] == "unknown"


def test_handwriting_variation_in_owner_name_still_matches():
    near_name = f.documents(land_record=f.extraction("land_record", owner_name="रमेश  यादव"))
    assert statuses(f.context(claim=f.claim(documents=near_name)))["documents_match_records"] == "pass"


# --- Payout --------------------------------------------------------------------------


def test_slabs_pick_highest_threshold_reached():
    slabs = (Slab(100, 25), Slab(150, 50), Slab(200, 100))
    assert slab_percent(99.9, slabs)[0] == 0
    assert slab_percent(150, slabs)[0] == 50
    assert slab_percent(260, slabs)[0] == 100
    assert slab_percent(None, slabs)[0] == 0


def test_excess_rain_payout_uses_rain_slab():
    ctx = f.context(claim=f.claim(peril=Peril.EXCESS_RAIN))
    quote = product.payout_quote(ctx, [f.evidence("weather", Signal.SUPPORTS, max_24h_mm=162.0)])
    assert (quote.payout_percent, quote.amount_inr) == (50, 24000)


def test_flood_payout_takes_better_of_radar_and_rain():
    ev = [
        f.evidence("weather", Signal.INCONCLUSIVE, max_24h_mm=40.0),
        f.evidence("satellite", Signal.SUPPORTS, flooded_fraction=0.55),
    ]
    quote = product.payout_quote(f.context(), ev)
    assert quote.payout_percent == 100
    assert "Radar" in quote.basis


def test_flood_without_any_trigger_pays_nothing():
    quote = product.payout_quote(f.context(), [f.evidence("weather", Signal.INCONCLUSIVE, max_24h_mm=12.0)])
    assert quote.amount_inr == 0


def test_hailstorm_pays_flat_rate():
    ctx = f.context(claim=f.claim(peril=Peril.HAILSTORM))
    assert product.payout_quote(ctx, []).payout_percent == CropTermSheet().hailstorm_flat_percent
