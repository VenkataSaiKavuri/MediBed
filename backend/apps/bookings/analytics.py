"""
Analytics for a hospital admin's own dashboard. Occupancy is derived from current bed
inventory (total vs. available right now) since there's no historical snapshot table of
bed counts over time — booking volume trends are the honest substitute for "trends" here,
computed from actual Booking rows rather than pretending to have data we don't.
"""
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.hospitals.models import BedInventory

from .models import Booking, BookingStatus

DEFAULT_TREND_DAYS = 30


def get_occupancy_stats(hospital_id):
    """Current utilization per bed type — (total - available) / total, as a percentage."""
    beds = BedInventory.objects.filter(hospital_id=hospital_id)
    stats = []
    for bed in beds:
        occupied = bed.total_count - bed.available_count
        occupancy_pct = round((occupied / bed.total_count) * 100, 1) if bed.total_count > 0 else 0
        stats.append({
            "bed_type": bed.bed_type,
            "total": bed.total_count,
            "available": bed.available_count,
            "occupied": occupied,
            "occupancy_pct": occupancy_pct,
        })
    return stats


def get_booking_volume_by_day(hospital_id, days=DEFAULT_TREND_DAYS):
    """Count of bookings created per day over the last `days` days — the actual demand trend."""
    since = timezone.now() - timedelta(days=days)
    rows = (
        Booking.objects.filter(hospital_id=hospital_id, created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    return [{"date": row["day"].isoformat(), "count": row["count"]} for row in rows]


def get_no_show_rate(hospital_id, days=DEFAULT_TREND_DAYS):
    """
    No-show rate as a percentage of RESOLVED bookings (completed + no_show + cancelled) —
    deliberately excludes still-pending ones, since a booking that hasn't happened yet
    can't meaningfully count toward a reliability rate either way.
    """
    since = timezone.now() - timedelta(days=days)
    resolved_statuses = [BookingStatus.COMPLETED, BookingStatus.NO_SHOW, BookingStatus.CANCELLED]
    resolved = Booking.objects.filter(hospital_id=hospital_id, created_at__gte=since, status__in=resolved_statuses)
    total_resolved = resolved.count()
    no_shows = resolved.filter(status=BookingStatus.NO_SHOW).count()
    rate = round((no_shows / total_resolved) * 100, 1) if total_resolved > 0 else 0
    return {"no_show_rate_pct": rate, "no_show_count": no_shows, "resolved_count": total_resolved}


def get_status_breakdown(hospital_id, days=DEFAULT_TREND_DAYS):
    """How bookings from the last `days` days are distributed across statuses."""
    since = timezone.now() - timedelta(days=days)
    rows = (
        Booking.objects.filter(hospital_id=hospital_id, created_at__gte=since)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [{"status": row["status"], "count": row["count"]} for row in rows]


def get_full_analytics(hospital_id, days=DEFAULT_TREND_DAYS):
    return {
        "occupancy": get_occupancy_stats(hospital_id),
        "booking_volume": get_booking_volume_by_day(hospital_id, days),
        "no_show": get_no_show_rate(hospital_id, days),
        "status_breakdown": get_status_breakdown(hospital_id, days),
        "period_days": days,
    }
