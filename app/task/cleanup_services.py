from datetime import datetime, date
import threading
import time
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.services import Servizio

_CHECK_INTERVAL_SECONDS = 24 * 3600
_DEFAULT_MAX_RANGE_DAYS = 90


def _to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            # try full ISO parse
            return datetime.fromisoformat(value).date()
        except Exception:
            # fallback: take date part YYYY-MM-DD
            try:
                parts = value.split("T")[0].split(" ")[0]
                return datetime.strptime(parts, "%Y-%m-%d").date()
            except Exception:
                return None
    return None


def _should_delete_service(s, today: date, verbose: bool = False) -> bool:
    """
    Decision rules (updated to keep any service while 'now' is within [dataRichiesta, dataConsegna]):

    - If either dataRichiesta or dataConsegna is missing -> SKIP (do not delete).
    - If dataConsegna < dataRichiesta -> INCONSISTENT -> DELETE.
    - If today > dataConsegna -> EXPIRED -> DELETE.
    - Otherwise (today is between request and delivery, or today == delivery) -> KEEP.

    This ensures services with dataConsegna in the future (e.g. dataConsegna = dataRichiesta + 3 months)
    are not deleted while we're still inside that range.
    """
    dr_raw = getattr(s, "dataRichiesta", None)
    dc_raw = getattr(s, "dataConsegna", None)

    dr_date = _to_date(dr_raw)
    dc_date = _to_date(dc_raw)

    if verbose:
        print(
            f"[CLEANUP DEBUG] id={getattr(s,'id',None)} "
            f"dr_raw={dr_raw!r} dc_raw={dc_raw!r} parsed dr={dr_date} dc={dc_date} today={today}"
        )

    # if either missing -> skip (do not delete)
    if dr_date is None or dc_date is None:
        if verbose:
            print(f"[CLEANUP DEBUG] id={getattr(s,'id',None)} SKIP: missing date(s)")
        return False

    # inconsistent: delivery before request -> delete
    if dc_date < dr_date:
        if verbose:
            print(f"[CLEANUP DEBUG] id={getattr(s,'id',None)} DELETE: dc_date {dc_date} < dr_date {dr_date} (inconsistent)")
        return True

    # expired: delivery date is in the past relative to today -> delete
    if today > dc_date:
        if verbose:
            print(f"[CLEANUP DEBUG] id={getattr(s,'id',None)} DELETE: today {today} > dc_date {dc_date} (expired)")
        return True

    # Otherwise (today <= dc_date and today >= dr_date) -> keep
    if verbose:
        print(f"[CLEANUP DEBUG] id={getattr(s,'id',None)} KEEP: today {today} is within [dr={dr_date}, dc={dc_date}]")
    return False


def _delete_expired_services_once(db: Session, soft: bool = True,
                                  dry_run: bool = True, verbose: bool = True) -> int:
    """
    Single cleanup pass:
    - Consider only services with dataConsegna not null (we only evaluate those).
    - Delete (soft or hard) only when _should_delete_service returns True.
    """
    today = datetime.now().date()
    deleted_count = 0
    try:
        # load only services that have a dataConsegna (we only consider those)
        q = db.query(Servizio).filter(Servizio.dataConsegna != None)
        services = q.all()

        if verbose:
            print(f"[CLEANUP] checking {len(services)} services (dataConsegna != NULL). today={today}")

        for s in services:
            try:
                should_delete = _should_delete_service(s, today, verbose=verbose)
                if should_delete:
                    if dry_run:
                        if verbose:
                            print(f"[CLEANUP DRY] would delete id={getattr(s,'id',None)}")
                        deleted_count += 1
                    else:
                        if soft and hasattr(s, "is_deleted"):
                            if not getattr(s, "is_deleted", False):
                                setattr(s, "is_deleted", True)
                                db.add(s)
                                deleted_count += 1
                                if verbose:
                                    print(f"[CLEANUP] soft-deleted id={getattr(s,'id',None)}")
                        elif not soft:
                            db.delete(s)
                            deleted_count += 1
                            if verbose:
                                print(f"[CLEANUP] hard-deleted id={getattr(s,'id',None)}")
            except Exception as e:
                print(f"[CLEANUP] error handling service id={getattr(s,'id',None)}: {e}")

        if not dry_run and deleted_count > 0:
            db.commit()
        else:
            # if dry_run or nothing changed, rollback to leave session clean
            db.rollback()

        if verbose:
            print(f"[CLEANUP] pass completed: {deleted_count} services {'would be marked' if dry_run else 'marked/deleted'}")

        return deleted_count
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP] error during cleanup: {e}")
        return deleted_count


def run_cleanup_once(dry_run: bool = True, soft: bool = True,
                     verbose: bool = True) -> int:
    db = SessionLocal()
    try:
        return _delete_expired_services_once(db, soft=soft, dry_run=dry_run, verbose=verbose)
    finally:
        db.close()


def start_cleanup_background(interval_seconds: Optional[int] = None, soft: bool = True,
                             daemon: bool = True, dry_run: bool = False, verbose: bool = False):
    if interval_seconds is None:
        interval_seconds = _CHECK_INTERVAL_SECONDS

    def _run_loop():
        while True:
            try:
                db = SessionLocal()
                try:
                    _delete_expired_services_once(db, soft=soft, dry_run=dry_run, verbose=verbose)
                finally:
                    db.close()
            except Exception as e:
                print("[CLEANUP] scheduler error:", e)
            time.sleep(interval_seconds)

    t = threading.Thread(target=_run_loop, daemon=daemon)
    t.start()
    print(f"[CLEANUP] started background thread (interval={interval_seconds}s, soft={soft}, dry_run={dry_run})")
    return t