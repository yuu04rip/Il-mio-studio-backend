from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.documentazione import Documentazione
from app.models.enums import TipoServizio, StatoServizio
from app.services.gestore_backup import GestoreBackup

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
    def _generate_codice_servizio(self) -> str:
        """
        Usa la sequence Postgres servizio_code_seq per generare
        codice nel formato SERV-000123
        """
        try:
            seq = self.db.execute(text("SELECT nextval('servizio_code_seq')")).scalar()
            codice = f"SERV-{int(seq):06d}"
            return codice
        except Exception:
            # fallback: genera codice temporaneo con timestamp se la sequence non è disponibile
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            return f"SERV-{ts}"

    def aggiungi_servizio(self, cliente_id, tipo, codiceCorrente, codiceServizio,
                          dataRichiesta, dataConsegna, dipendente_id=None):
        # Popola snapshot nome/cognome cliente (se possibile)
        cliente_nome = None
        cliente_cognome = None
        try:
            cliente = self.db.get(Cliente, cliente_id)
            if cliente and getattr(cliente, "utente_id", None):
                user = self.db.get(User, cliente.utente_id)
                if user:
                    cliente_nome = user.nome
                    cliente_cognome = user.cognome
        except Exception:
            cliente_nome = None
            cliente_cognome = None

        # se codiceServizio non fornito o None -> generalo automaticamente
        if not codiceServizio:
            codiceServizio = self._generate_codice_servizio()

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
            is_deleted=False
        )
        self.db.add(servizio)
        self.db.flush()
        if dipendente_id:
            dip = self.db.get(DipendenteTecnico, dipendente_id)
            if dip:
                servizio.dipendenti.append(dip)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

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

    def inizializza_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio == StatoServizio.IN_LAVORAZIONE:
            return None
        servizio.statoServizio = StatoServizio.IN_LAVORAZIONE
        self.db.commit()
        self.db.refresh(servizio)
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