from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico, Contabile, Assistente
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.documentazione import Documentazione
from app.models.enums import TipoDipendenteTecnico, TipoServizio

from app.services.gestore_backup import GestoreBackup

class GestoreStudio:
    def __init__(self, db: Session):
        self.db = db
        self.backup = None  # Non inizializzo subito

        # Soft-delete "virtuale" (solo in memoria! Si perde a ogni nuovo oggetto gestore)
        self._servizi_virtualmente_eliminati = set()
        self._dipendenti_virtualmente_eliminati = set()

    # --- Inizializza archiviazione (GestoreBackup) ---
    def inizializza_archiviazione(self):
        self.backup = GestoreBackup(self.db)
        self.backup.setup_backup()

    # Liste - per UML
    def clienti(self):
        return self.db.query(Cliente).all()

    def dipendenti(self):
        return [d for d in self.db.query(DipendenteTecnico).all() if d.id not in self._dipendenti_virtualmente_eliminati]

    def servizi(self):
        return [s for s in self.db.query(Servizio).all() if s.id not in self._servizi_virtualmente_eliminati]

    # --- Dipendenti e Notai ---
    def aggiungi_dipendente(self, nome, cognome, email, password_hash, tipo: TipoDipendenteTecnico, numeroTelefonico=None, codice_notarile=None):
        ruolo = Role.NOTAIO if tipo == TipoDipendenteTecnico.NOTAIO else Role.DIPENDENTE
        user = User(
            nome=nome,
            cognome=cognome,
            email=email,
            password=password_hash,
            ruolo=ruolo,
            numeroTelefonico=numeroTelefonico,
        )
        self.db.add(user)
        self.db.flush()
        if tipo == TipoDipendenteTecnico.NOTAIO:
            dip = Notaio(utente_id=user.id, codice_notarile=codice_notarile, tipo=tipo)
        elif tipo == TipoDipendenteTecnico.CONTABILE:
            dip = Contabile(utente_id=user.id, tipo=tipo)
        elif tipo == TipoDipendenteTecnico.ASSISTENTE:
            dip = Assistente(utente_id=user.id, tipo=tipo)
        else:
            dip = DipendenteTecnico(utente_id=user.id, tipo=tipo)
        self.db.add(dip)
        self.db.commit()
        self.db.refresh(dip)
        return dip

    def elimina_dipendente(self, dipendente_id: int):
        """Soft delete: rimuove solo dalla lista virtuale."""
        self._dipendenti_virtualmente_eliminati.add(dipendente_id)
        return True

    def distruggi_dipendente(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
         return False
        # Elimina il Cliente se esiste
        cliente = self.db.query(Cliente).filter(Cliente.utente_id == dip.utente_id).first()
        if cliente:
            self.db.delete(cliente)
    # Elimina l'utente associato
        user = self.db.get(User, dip.utente_id)
        if user:
         self.db.delete(user)
         self.db.delete(dip)
         self.db.commit()
        return True

    def get_dipendenti(self):
        return self.dipendenti()

    def get_notai(self):
        return self.db.query(Notaio).all()

    # --- Clienti ---
    def get_clienti(self):
        return self.clienti()

    def cerca_cliente_per_nome(self, nome: str):
        return self.db.query(Cliente).join(Cliente.utente).filter(User.nome == nome).first()
    def search_clienti(self, q: str):
    # Cerca sia su nome che su cognome (case insensitive)
     return self.db.query(Cliente).join(Cliente.utente).filter(
        (User.nome.ilike(f"%{q}%")) | (User.cognome.ilike(f"%{q}%"))
    ).all()

    # --- Servizi ---
    def aggiungi_servizio(self, cliente_id, tipo: TipoServizio, codiceCorrente, codiceServizio, dataRichiesta, dataConsegna):
        servizio = Servizio(
            cliente_id=cliente_id,
            tipo=tipo,
            codiceCorrente=codiceCorrente,
            codiceServizio=codiceServizio,
            statoServizio=False,
            dataRichiesta=dataRichiesta,
            dataConsegna=dataConsegna,
        )
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def elimina_servizio(self, servizio_id: int):
        """Soft delete: rimuove solo dalla lista virtuale."""
        self._servizi_virtualmente_eliminati.add(servizio_id)
        return True

    def distruggi_servizio(self, servizio_id: int):
        """Hard delete: elimina davvero dal database."""
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return False
        self.db.delete(servizio)
        self.db.commit()
        return True

    def cerca_servizio_per_codice(self, codice_servizio: int):
        # Mostra solo se non è stato soft deleted
        servizio = self.db.query(Servizio).filter(Servizio.codiceServizio == codice_servizio).first()
        if servizio and servizio.id not in self._servizi_virtualmente_eliminati:
            return servizio
        return None

    def visualizza_servizi(self):
        return self.servizi()

    # --- SERVIZI ARCHIVIATI: delega a GestoreBackup ---
    def archivia_servizio(self, servizio_id: int):
        if self.backup is None:
            self.inizializza_archiviazione()
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            return None
        return self.backup.archivia_servizio(servizio)

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

    # --- Documentazione ---
    def aggiungi_documentazione(self, cliente_id: int, filename: str, tipo, path: str):
        doc = Documentazione(
            cliente_id=cliente_id,
            filename=filename,
            tipo=tipo,
            path=path,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def visualizza_documentazione_cliente(self, cliente_id: int):
        return self.db.query(Documentazione).filter(Documentazione.cliente_id == cliente_id).all()

    def sostituisci_documentazione(self, doc_id: int, filename: str = None, path: str = None):
        doc = self.db.get(Documentazione, doc_id)
        if not doc:
            return None
        if filename: doc.filename = filename
        if path: doc.path = path
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # --- Associazioni e altro ---
    def aggiungi_dipendente_al_servizio(self, servizio_id: int, dipendente_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not servizio or not dip:
            return False
        servizio.dipendenti.append(dip)
        self.db.commit()
        return True

    def visualizza_lavoro_da_svolgere(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [s for s in dip.servizi if not s.statoServizio and s.id not in self._servizi_virtualmente_eliminati]

    def visualizza_servizi_inizializzati(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return []
        return [s for s in dip.servizi if s.statoServizio and s.id not in self._servizi_virtualmente_eliminati]

    # --- Placeholder per invio credenziali ---
    def invia_credenziali(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            return False
        # Qui andrebbe la logica di invio email con le credenziali
        return True

    # --- Modifica documentazione generica ---
    def modifica_documentazione_per_servizio(self, doc_id: int, nuova_descrizione: str = None, nuovo_tipo=None, nuovo_filename=None):
        doc = self.db.get(Documentazione, doc_id)
        if not doc:
            return None
        if nuova_descrizione: doc.descrizione = nuova_descrizione
        if nuovo_tipo: doc.tipo = nuovo_tipo
        if nuovo_filename: doc.filename = nuovo_filename
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc
    def visualizza_servizi_cliente(self, cliente_id: int):
        # Ritorna tutti i servizi per uno specifico cliente (escludendo i soft-deleted)
        return [
            s for s in self.db.query(Servizio).filter(Servizio.cliente_id == cliente_id).all()
            if s.id not in self._servizi_virtualmente_eliminati
        ]