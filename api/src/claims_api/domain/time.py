from datetime import timedelta, timezone

# India Standard Time has no daylight saving, so a fixed offset is exact.
IST = timezone(timedelta(hours=5, minutes=30), "IST")
