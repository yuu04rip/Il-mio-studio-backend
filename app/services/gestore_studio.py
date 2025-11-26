from typing import Optional

from sqlalchemy import text, select, insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import calendar
from app.models.cliente_counters import ClienteCounters
from app.models.user import User
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.documentazione import Documentazione
from app.models.enums import TipoServizio, StatoServizio
from app.services.gestore_backup import GestoreBackup


def _add_months(dt: datetime, months: int) -> datetime:
    """
    Add `months` months to datetime `dt`. Keeps time part.
    If the target month has fewer days, it clamps to the last day of the month.
    """
    if dt is None:
        return None
    # handle naive and aware datetimes similarly (preserve tzinfo if present)
    tz = getattr(dt, "tzinfo", None)
    year = dt.year
    month = dt.month + months
    # normalize year/month
    year += (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = dt.day
    # clamp day to last day of target month
    last_day = calendar.monthrange(year, month)[1]
    day = min(day, last_day)
    return datetime(year, month, day, dt.hour, dt.minute, dt.second, dt.microsecond, tzinfo=tz)


class GestoreStudio:
    def __init__(self, db: Session):
        self.db = db
        self.backup = None

    # --- Archivio ---
    def inizializza_archiviazione(self):
        self.backup = GestoreBackup(self.db)
        self.backup.setup_backup()

    # --- Dipendenti & Notai ---
    def elimina_dipendente(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return False
        return True

    def distruggi_dipendente(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return False
        cliente = self.db.query(Cliente).filter(Cliente.utente_id == dip.utente_id).first()
        if cliente:
            self.db.delete(cliente)
        user = self.db.get(User, dip.utente_id)
        if user:
            self.db.delete(user)
        self.db.delete(dip)
        self.db.commit()
        return True

    def get_dipendenti(self):
        return self.db.query(DipendenteTecnico).all()

    def get_notai(self):
        return self.db.query(Notaio).all()

    # --- Clienti ---
    def get_clienti(self):
        return self.db.query(Cliente).all()

    def cerca_cliente_per_nome(self, nome: str):
        return self.db.query(Cliente).join(Cliente.utente).filter(User.nome == nome).first()

    def search_clienti(self, q: str):
        """
        Cerca clienti per nome o cognome e restituisce una lista di dict
        con i campi minimi utili al frontend: id, nome, cognome, email.
        """
        if not q:
            return []

        qlike = f"%{q}%"
        # join Cliente -> User (assumendo relazione cliente.utente)
        clienti = (
            self.db.query(Cliente)
            .join(Cliente.utente)  # relazione ORM: Cliente.utente
            .filter(
                (User.nome.ilike(qlike)) |
                (User.cognome.ilike(qlike))
            )
            .all()
        )

        results = []
        for c in clienti:
            u = getattr(c, "utente", None)
            results.append({
                "id": getattr(c, "id", None),
                "nome": getattr(u, "nome", "") if u else "",
                "cognome": getattr(u, "cognome", "") if u else "",
                "email": getattr(u, "email", "") if u else ""
            })
        return results

    # --- Servizi ---
    # modifica _generate_codice_servizio: rimane come prima ma chiarire il return
    def _generate_codice_servizio(self) -> tuple[str, Optional[int]]:
        from datetime import datetime
        # Try Postgres-style nextval
        try:
            seq = self.db.execute(text("SELECT nextval('servizio_code_seq')")).scalar()
            if seq is not None:
                codice = f"SERV-{int(seq):06d}"
                return codice, int(seq)
        except Exception:
            pass

        # Try MySQL / MariaDB: INSERT INTO servizio_code_seq () VALUES (); SELECT LAST_INSERT_ID();
        try:
            self.db.execute(text("INSERT INTO servizio_code_seq () VALUES ();"))
            last = self.db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            if last:
                seq_id = int(last)
                codice = f"SERV-{seq_id:06d}"
                return codice, seq_id
        except Exception:
            pass

        # fallback: timestamp (seq_id=None)
        ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"SERV-{ts}", None

    def _get_next_codice_corrente_for_cliente(self, cliente_id: int) -> int:
        """
        Restituisce il prossimo codiceCorrente per il cliente (atomico).
        Questa funzione NON apre una transazione propria: deve essere chiamata
        dentro una transazione (es. with self.db.begin()) che garantisca il lock.
        """
        try:
            # leggi riga con lock FOR UPDATE (assume che il caller abbia begun la transaction)
            row = self.db.execute(
                select(ClienteCounters).where(ClienteCounters.cliente_id == cliente_id).with_for_update()
            ).scalar_one_or_none()

            if row is None:
                # non esiste: inseriamo riga con last_value = 2 (next sarà 1 restituito, next disponibile = 2)
                self.db.execute(
                    insert(ClienteCounters).values(cliente_id=cliente_id, last_value=2)
                )
                return 1
            else:
                # last_value contiene il NEXT da restituire
                next_val = int(row.last_value)
                # incrementa last_value -> next_val + 1
                self.db.execute(
                    update(ClienteCounters)
                    .where(ClienteCounters.cliente_id == cliente_id)
                    .values(last_value=next_val + 1)
                )
                return next_val
        except SQLAlchemyError:
            # log ed eventualmente rilancia
            raise

    def aggiungi_servizio(
            self,
            cliente_id,
            tipo,
            codiceCorrente: Optional[int] = None,
            codiceServizio: Optional[str] = None,
            dataRichiesta=None,
            dataConsegna=None,
            dipendente_id: Optional[int] = None,
    ):
        """
        Crea un servizio e, se è il PRIMO servizio per quel cliente (non conteggiando is_deleted),
        assegna il cliente al dipendente creatore (se fornito dipendente_id).
        L'assegnazione è effettuata in modo difensivo: cerca il campo più probabile su Cliente
        (responsabile_id, responsabile, responsabile_tecnico, dipendente_id, owner_id) e lo imposta.

        Nuova regola: se dataConsegna è None, viene impostata a dataRichiesta + 3 mesi.
        """
        # snapshot cliente (nome/cognome) per il servizio
        cliente_nome = None
        cliente_cognome = None
        cliente_obj = None
        try:
            cliente = self.db.get(Cliente, cliente_id)
            cliente_obj = cliente
            if cliente and getattr(cliente, "utente_id", None):
                user = self.db.get(User, cliente.utente_id)
                if user:
                    cliente_nome = user.nome
                    cliente_cognome = user.cognome
        except Exception:
            cliente_nome = None
            cliente_cognome = None

        try:
            # --- controllo se è il PRIMO servizio per il cliente (escludiamo is_deleted) ---
            try:
                existing_count = self.db.query(Servizio).filter(
                    Servizio.cliente_id == cliente_id,
                    Servizio.is_deleted == False
                ).count()
            except Exception:
                existing_count = 0

            # se non ho dataRichiesta, imposto ad ora (naive datetime)
            if dataRichiesta is None:
                dataRichiesta = datetime.now()

            # se dataConsegna non è fornita, impostala a dataRichiesta + 3 mesi
            if dataConsegna is None:
                dataConsegna = _add_months(dataRichiesta, 3)

            # Non apriamo una nuova transaction: usiamo quella fornita dalla dependency
            # se manca codiceCorrente -> ottieni il prossimo per il cliente
            if not codiceCorrente:
                codiceCorrente = self._get_next_codice_corrente_for_cliente(cliente_id)

            # se manca codiceServizio -> genera
            if not codiceServizio:
                codiceServizio, _seq = self._generate_codice_servizio()

            # crea l'oggetto Servizio (FUORI dall'if precedente)
            servizio = Servizio(
                cliente_id=cliente_id,
                tipo=tipo,
                codiceCorrente=codiceCorrente,
                codiceServizio=codiceServizio,
                cliente_nome=cliente_nome,
                cliente_cognome=cliente_cognome,
                statoServizio=StatoServizio.CREATO,
                dataRichiesta=dataRichiesta,
                dataConsegna=dataConsegna,
                is_deleted=False,
                creato_da_id=dipendente_id,
            )

            self.db.add(servizio)
            self.db.flush()  # assicura che servizio.id sia disponibile

            # assegna dipendente se fornito
            if dipendente_id:
                dip = self.db.get(DipendenteTecnico, dipendente_id)
                if dip:
                    servizio.dipendenti.append(dip)

            # --- Se è il primo servizio e abbiamo dipendente_id, assegna il cliente ---
            if existing_count == 0 and dipendente_id and cliente_obj is not None:
                try:
                    dip = self.db.get(DipendenteTecnico, dipendente_id)
                    # preferiamo assegnare l'oggetto relazione se possibile
                    if dip is not None:
                        if hasattr(cliente_obj, 'responsabile'):
                            cliente_obj.responsabile = dip
                        elif hasattr(cliente_obj, 'responsabile_tecnico'):
                            cliente_obj.responsabile_tecnico = dip
                        elif hasattr(cliente_obj, 'responsabile_id'):
                            cliente_obj.responsabile_id = dipendente_id
                        elif hasattr(cliente_obj, 'dipendente_id'):
                            cliente_obj.dipendente_id = dipendente_id
                        elif hasattr(cliente_obj, 'owner_id'):
                            cliente_obj.owner_id = dipendente_id
                        else:
                            # fallback: crea/assegna un attributo responsabile_id se possibile
                            try:
                                setattr(cliente_obj, 'responsabile_id', dipendente_id)
                            except Exception:
                                # non critico: loggare e proseguire
                                print(f"[GestoreStudio] warning: impossibile impostare responsabile per cliente {cliente_id}")
                        # assicurati che il cliente sia persistito nell'unità di lavoro
                        self.db.add(cliente_obj)

                        # Commit esplicito per rendere subito persistente l'assegnazione
                        try:
                            self.db.commit()
                            # refresh per sicurezza
                            try:
                                self.db.refresh(cliente_obj)
                            except Exception:
                                pass
                        except Exception as e:
                            # se il commit fallisce, rollback e log; non facciamo fallire la creazione del servizio
                            self.db.rollback()
                            print(f"[GestoreStudio] warning: commit assegnazione cliente fallito: {e}")
                    else:
                        # dip non trovato: proviamo ad impostare il campo id raw se esiste
                        if hasattr(cliente_obj, 'responsabile_id'):
                            cliente_obj.responsabile_id = dipendente_id
                            self.db.add(cliente_obj)
                            try:
                                self.db.commit()
                                try:
                                    self.db.refresh(cliente_obj)
                                except Exception:
                                    pass
                            except Exception as e:
                                self.db.rollback()
                                print(f"[GestoreStudio] warning: commit assegnazione cliente fallito (raw id): {e}")
                except Exception as e:
                    # non facciamo fallire la creazione del servizio per un errore di assegnazione
                    print(f"[GestoreStudio] warning: errore assegnazione responsabile cliente {cliente_id}: {e}")

            # refresh (oggetto ancora attached alla sessione)
            try:
                self.db.refresh(servizio)
            except Exception:
                # non critico: se refresh fallisce, continuiamo comunque
                pass

            # NOTA: commit è gestito dal caller / dal dependency get_db se non abbiamo già fatto commit sopra
            return servizio

        except SQLAlchemyError:
            # log e rilancia per far vedere il traceback nel server
            raise

    def elimina_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return False
        servizio.is_deleted = True
        self.db.commit()
        return True

    def distruggi_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return False
        self.db.delete(servizio)
        self.db.commit()
        return True

    def cerca_servizio_per_codice(self, codice_servizio: str):
        # codice_servizio ora stringa (es. "SERV-000123")
        return self.db.query(Servizio).filter(Servizio.codiceServizio == codice_servizio).first()

    def visualizza_servizi(self):
        return self.db.query(Servizio).filter(Servizio.is_deleted == False).all()

    # --- Archivio servizi ---
    def archivia_servizio(self, servizio_id: int):
        if self.backup is None:
            self.inizializza_archiviazione()
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return None
        return self.backup.archivia_servizio(servizio)

    def servizi_per_notaio(self):
        return self.db.query(Servizio).filter(Servizio.is_deleted == False).all()

    def modifica_servizio_archiviato(self, servizio_id: int, statoServizio: bool):
        if self.backup is None:
            self.inizializza_archiviazione()
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return None
        return self.backup.modifica_servizio_archiviato(servizio, statoServizio)

    def visualizza_servizi_archiviati(self):
        if self.backup is None:
            self.inizializza_archiviazione()
        return self.backup.mostra_servizi_archiviati()

    def inizializza_servizio(self, servizio_id: int, actor_dipendente_id: Optional[int] = None):
        """
        Inizializza il servizio (passa CREATO -> IN_LAVORAZIONE).
        Se actor_dipendente_id è fornito e il cliente associato non ha responsabile, assegna il cliente a quel dipendente.
        """
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio == StatoServizio.IN_LAVORAZIONE:
            return None

        servizio.statoServizio = StatoServizio.IN_LAVORAZIONE

        # Prova ad assegnare il cliente se non ha responsabile e abbiamo actor_dipendente_id
        try:
            if actor_dipendente_id:
                cliente = None
                try:
                    cliente = self.db.get(Cliente, servizio.cliente_id)
                except Exception:
                    cliente = None

                if cliente:
                    has_responsabile = False
                    if hasattr(cliente, 'responsabile_id') and getattr(cliente, 'responsabile_id', None):
                        has_responsabile = True
                    elif hasattr(cliente, 'responsabile') and getattr(cliente, 'responsabile', None):
                        has_responsabile = True
                    elif hasattr(cliente, 'dipendente_id') and getattr(cliente, 'dipendente_id', None):
                        has_responsabile = True
                    elif hasattr(cliente, 'owner_id') and getattr(cliente, 'owner_id', None):
                        has_responsabile = True

                    if not has_responsabile:
                        dip = self.db.get(DipendenteTecnico, actor_dipendente_id)
                        if dip:
                            try:
                                if hasattr(cliente, 'responsabile'):
                                    cliente.responsabile = dip
                                elif hasattr(cliente, 'responsabile_tecnico'):
                                    cliente.responsabile_tecnico = dip
                                elif hasattr(cliente, 'responsabile_id'):
                                    cliente.responsabile_id = actor_dipendente_id
                                elif hasattr(cliente, 'dipendente_id'):
                                    cliente.dipendente_id = actor_dipendente_id
                                elif hasattr(cliente, 'owner_id'):
                                    cliente.owner_id = actor_dipendente_id
                                else:
                                    try:
                                        setattr(cliente, 'responsabile_id', actor_dipendente_id)
                                    except Exception:
                                        pass
                                self.db.add(cliente)
                                # persist immediatamente in modo che il GET clienti?onlyMine=true veda l'assegnazione
                                try:
                                    self.db.commit()
                                    try:
                                        self.db.refresh(cliente)
                                    except Exception:
                                        pass
                                except Exception:
                                    self.db.rollback()
                            except Exception as e:
                                print(f"[GestoreStudio] warning: errore assegnazione cliente in inizializza_servizio: {e}")
        except Exception as e:
            print(f"[GestoreStudio] warning: errore durante assegnazione cliente in inizializza_servizio outer: {e}")

        # Persisti stato servizio e refresh
        try:
            self.db.add(servizio)
            self.db.commit()
            self.db.refresh(servizio)
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass
            return None

        return servizio

    def visualizza_servizi_completati(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [
            s for s in dip.servizi
            if s.statoServizio in [StatoServizio.APPROVATO, StatoServizio.RIFIUTATO, StatoServizio.CONSEGNATO]
               and not s.is_deleted
        ]

    def inoltra_servizio_notaio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_LAVORAZIONE:
            return None
        servizio.statoServizio = StatoServizio.IN_ATTESA_APPROVAZIONE
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def servizi_da_approvare(self):
        return self.db.query(Servizio).filter(Servizio.statoServizio == StatoServizio.IN_ATTESA_APPROVAZIONE).all()

    def approva_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_ATTESA_APPROVAZIONE:
            return None
        servizio.statoServizio = StatoServizio.APPROVATO
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def visualizza_servizi_altri_dipendenti(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [
            s for s in dip.servizi
            if getattr(s, "owner_id", None) != dipendente_id
        ]

    def rifiuta_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_ATTESA_APPROVAZIONE:
            return None
        servizio.statoServizio = StatoServizio.RIFIUTATO
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def assegna_servizio(self, servizio_id: int, dipendente_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        dipendente = self.db.get(DipendenteTecnico, dipendente_id)
        if not servizio or not dipendente:
            return False
        if dipendente not in servizio.dipendenti:
            servizio.dipendenti.append(dipendente)
        self.db.commit()
        self.db.refresh(servizio)
        return True

    # --- Documentazione ---
    def aggiungi_documentazione(self, cliente_id: int, filename: str, tipo, data: bytes, servizio_id: int = None):
        doc = Documentazione(
            cliente_id=cliente_id,
            servizio_id=servizio_id,
            filename=filename,
            tipo=tipo,
            data=data,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def sostituisci_documentazione(self, doc_id: int, filename: str = None, data: bytes = None):
        doc = self.db.get(Documentazione, doc_id)
        if not doc:
            return None
        if filename:
            doc.filename = filename
        if data:
            doc.data = data
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def visualizza_documentazione_cliente(self, cliente_id: int):
        return self.db.query(Documentazione).filter(Documentazione.cliente_id == cliente_id).all()

    def visualizza_lavoro_da_svolgere(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [
            s for s in dip.servizi
            if s.statoServizio == StatoServizio.CREATO
        ]

    def visualizza_servizi_inizializzati(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [
            s for s in dip.servizi
            if s.statoServizio == StatoServizio.IN_LAVORAZIONE
        ]

    def visualizza_servizi_cliente(self, cliente_id: int):
        return self.db.query(Servizio).filter(
            Servizio.cliente_id == cliente_id,
            Servizio.is_deleted == False
        ).all()

    def modifica_servizio(self, servizio_id: int, **kwargs):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return None
        for key, value in kwargs.items():
            if hasattr(servizio, key) and value is not None:
                if key == "tipo":
                    try:
                        value = TipoServizio(value)
                    except ValueError:
                        continue
                setattr(servizio, key, value)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio