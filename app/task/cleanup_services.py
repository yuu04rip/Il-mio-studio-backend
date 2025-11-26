from datetime import datetime, date, timedelta
import threading
import time
from typing import Optional

from sqlalchemy.orm import Session

# Adatta l'import della sessione al tuo progetto
from app.db.session import SessionLocal

# importa modello Servizio e l'enum StatoServizio se necessario
from app.models.services import Servizio

_CHECK_INTERVAL_SECONDS = 24 * 3600  # default: run once per day
_DEFAULT_MAX_RANGE_DAYS = 90  # circa 3 mesi


def _should_delete_service(s, today: date, max_range_days: int) -> bool:
    """
    Decide se il servizio `s` deve essere cancellato, secondo le regole:
      - se manca dataRichiesta o dataConsegna -> non eliminare (skip)
      - se dataConsegna < today -> scaduto => delete
      - se dataConsegna < dataRichiesta -> inconsistente => delete
      - se (dataConsegna - dataRichiesta) > max_range_days => delete (range > 3 mesi)
    Ritorna True se deve essere eliminato.
    """
    try:
        dr = getattr(s, "dataRichiesta", None)
        dc = getattr(s, "dataConsegna", None)
        if dr is None or dc is None:
            return False

        # normalizza a date
        if isinstance(dr, datetime):
            dr_date = dr.date()
        elif isinstance(dr, date):
            dr_date = dr
        else:
            return False

        if isinstance(dc, datetime):
            dc_date = dc.date()
        elif isinstance(dc, date):
            dc_date = dc
        else:
            return False

        # scaduto rispetto a oggi
        if dc_date < today:
            return True

        # consegna prima della richiesta -> inconsistente
        if dc_date < dr_date:
            return True

        # range troppo ampio tra richiesta e consegna
        delta_days = (dc_date - dr_date).days
        if delta_days > max_range_days:
            return True

        return False
    except Exception as e:
        # in caso di errori nella valutazione, non eliminare per sicurezza
        print(f"[CLEANUP] errore valutazione servizio id={getattr(s, 'id', None)}: {e}")
        return False


def _delete_expired_services_once(db: Session, soft: bool = True, max_range_days: int = _DEFAULT_MAX_RANGE_DAYS) -> int:
    """
    Esegue una singola passata di pulizia:
    - Scorre tutti i servizi che hanno dataRichiesta e/o dataConsegna valorizzate.
    - Applica le regole di cancellazione definite in _should_delete_service.
    - Di default effettua soft-delete impostando is_deleted=True se il campo esiste;
      se soft=False elimina fisicamente la riga.

    Ritorna il numero di servizi marcati/eliminati.
    """
    today = datetime.now().date()
    deleted_count = 0
    try:
        # carichiamo i servizi con almeno una delle date per limitare i risultati
        q = db.query(Servizio).filter(
            (Servizio.dataConsegna != None) | (Servizio.dataRichiesta != None)
        )
        services = q.all()
        for s in services:
            try:
                if _should_delete_service(s, today, max_range_days):
                    if soft and hasattr(s, "is_deleted"):
                        setattr(s, "is_deleted", True)
                        db.add(s)
                        deleted_count += 1
                    elif not soft:
                        db.delete(s)
                        deleted_count += 1
            except Exception as e:
                print(f"[CLEANUP] errore gestione servizio id={getattr(s, 'id', None)}: {e}")
        db.commit()
        print(f"[CLEANUP] pass completato: {deleted_count} servizi {'soft-deleted' if soft else 'deleted'} (tutti gli stati; range max {max_range_days} giorni)")
        return deleted_count
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP] errore durante cleanup: {e}")
        return deleted_count


def run_cleanup_once(soft: bool = True, max_range_days: int = _DEFAULT_MAX_RANGE_DAYS) -> int:
    """
    Esegue il cleanup una volta (utile per test/manual run).
    """
    db = SessionLocal()
    try:
        return _delete_expired_services_once(db, soft=soft, max_range_days=max_range_days)
    finally:
        db.close()


def start_cleanup_background(interval_seconds: Optional[int] = None, soft: bool = True,
                             max_range_days: int = _DEFAULT_MAX_RANGE_DAYS, daemon: bool = True):
    """
    Avvia un thread in background che esegue periodicamente il cleanup.

    Parametri:
      - interval_seconds: intervallo tra le esecuzioni (default 24h)
      - soft: se True impostare is_deleted=True (se presente), altrimenti eliminazione fisica
      - max_range_days: massimo intervallo consentito tra dataRichiesta e dataConsegna (default 90 giorni)
      - daemon: flag per thread daemon

    Esempio (main.py):
        start_cleanup_background()  # ogni 24h, soft-delete, range 90 giorni

    Per test rapido:
        start_cleanup_background(interval_seconds=60, soft=True, max_range_days=90)
    """
    if interval_seconds is None:
        interval_seconds = _CHECK_INTERVAL_SECONDS

    def _run_loop():
        while True:
            try:
                db = SessionLocal()
                try:
                    _delete_expired_services_once(db, soft=soft, max_range_days=max_range_days)
                finally:
                    db.close()
            except Exception as e:
                print("[CLEANUP] scheduler error:", e)
            time.sleep(interval_seconds)

    t = threading.Thread(target=_run_loop, daemon=daemon)
    t.start()
    print(f"[CLEANUP] started background thread (interval={interval_seconds}s, soft={soft}, max_range_days={max_range_days})")
    return t