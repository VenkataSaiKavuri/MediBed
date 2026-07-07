"""
Shared nearest-hospital matching logic — used by both the patient-facing
GET /api/hospitals/nearest/ endpoint (Day 22) and the emergency auto-escalation command
(Day 24), so there's exactly one place that defines "which hospital is the best next match."
"""
from .geo import haversine_km
from .models import Hospital


def find_ranked_hospitals(lat, lng, bed_type=None, exclude_ids=None, limit=10):
    """
    Returns a list of (distance_km, Hospital) tuples, sorted nearest-first.
    - Only verified hospitals are considered.
    - If bed_type is given, hospitals with zero available beds of that type are excluded
      entirely (not just ranked lower) — showing/offering a hospital with no stock wastes
      exactly the time this feature exists to save.
    - exclude_ids lets the escalation flow skip hospitals already tried for this booking.
    """
    exclude_ids = set(exclude_ids or [])
    hospitals = Hospital.objects.filter(is_verified=True).exclude(id__in=exclude_ids).prefetch_related("bed_inventory")

    results = []
    for hospital in hospitals:
        if bed_type:
            bed = next((b for b in hospital.bed_inventory.all() if b.bed_type == bed_type), None)
            if not bed or bed.available_count <= 0:
                continue

        distance = haversine_km(lat, lng, hospital.latitude, hospital.longitude)
        results.append((distance, hospital))

    results.sort(key=lambda pair: pair[0])
    return results[:limit]


def find_next_hospital(booking):
    """
    Convenience wrapper for the escalation flow: given a booking, finds the single
    best next hospital to reassign it to — nearest (if we have patient coordinates) with
    live availability for the booking's bed type, excluding the current hospital and every
    hospital already tried. Returns None if nothing suitable is left.
    """
    exclude_ids = set(booking.previous_hospital_ids or []) | {booking.hospital_id}

    if booking.patient_latitude is not None and booking.patient_longitude is not None:
        ranked = find_ranked_hospitals(
            booking.patient_latitude, booking.patient_longitude,
            bed_type=booking.bed_type, exclude_ids=exclude_ids, limit=1,
        )
        return ranked[0][1] if ranked else None

    # No patient coordinates captured (geolocation was denied/unavailable) — fall back to
    # any verified hospital with stock, since distance can't be computed without a location.
    from .models import Hospital
    candidates = Hospital.objects.filter(is_verified=True).exclude(id__in=exclude_ids).prefetch_related("bed_inventory")
    for hospital in candidates:
        bed = next((b for b in hospital.bed_inventory.all() if b.bed_type == booking.bed_type), None)
        if bed and bed.available_count > 0:
            return hospital
    return None
