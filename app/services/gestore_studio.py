from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico, Contabile, Assistente
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.documentazione import Documentazione
from app.models.enums import TipoDipendenteTecnico, TipoServizio, StatoServizio
from app.models.tables import dipendente_servizio
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

    # --- Liste - per UML ---
    def clienti(self):
        return self.db.query(Cliente).all()

    def dipendenti(self):
        return [
            d for d in self.db.query(DipendenteTecnico).all()
            if d.id not in self._dipendenti_virtualmente_eliminati
        ]

    def servizi(self):
        return self.db.query(Servizio).filter(Servizio.is_deleted == False).all()

    # --- Dipendenti e Notai ---
    def aggiungi_dipendente(
            self, nome, cognome, email, password_hash,
            tipo: TipoDipendenteTecnico, numeroTelefonico=None, codice_notarile=None
    ):
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
    def aggiungi_servizio(
            self, cliente_id, tipo, codiceCorrente, codiceServizio,
            dataRichiesta, dataConsegna, dipendente_id=None
    ):
        servizio = Servizio(
            cliente_id=cliente_id,
            tipo=tipo,
            codiceCorrente=codiceCorrente,
            codiceServizio=codiceServizio,
            statoServizio=StatoServizio.CREATO,
            dataRichiesta=dataRichiesta,
            dataConsegna=dataConsegna,
            is_deleted=False
        )
        self.db.add(servizio)
        self.db.flush()  # crea l'id per la relazione
        if dipendente_id:
            dip = self.db.get(DipendenteTecnico, dipendente_id)
            print("Dip trovato?", dip)
            if dip:
                servizio.dipendenti.append(dip)
                print("Dopo append:", servizio.dipendenti)  # aggiorna la tabella di relazione!
        self.db.commit()
        print("Servizio id:", servizio.id, "Dipendenti:", [d.id for d in servizio.dipendenti])
        self.db.refresh(servizio)
        return servizio

    def elimina_servizio(self, servizio_id: int):
        """Soft-delete persistente nel DB"""
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            print(f"[DEBUG] Servizio {servizio_id} non trovato per soft delete")
            return False
        servizio.is_deleted = True
        self.db.commit()
        print(f"[DEBUG] Servizio {servizio_id} marcato come eliminato (is_deleted=True)")
        return True

    def distruggi_servizio(self, servizio_id: int):
        """Hard delete: elimina davvero dal database."""
        print(f"Hard delete servizio: {servizio_id}")
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
            print("Servizio non trovato per hard delete.")
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

    def inizializza_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio == StatoServizio.IN_LAVORAZIONE:
            print(f"Impossibile inizializzare servizio {servizio_id}: non trovato o già in lavorazione")
            return None
        print(f"Inizializzo servizio {servizio_id}")
        servizio.statoServizio = StatoServizio.IN_LAVORAZIONE
        self.db.commit()
        self.db.refresh(servizio)
        return servizio
    def visualizza_servizi_completati(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
         return []

    # Mostra servizi in stati finali
        servizi = [
         s for s in dip.servizi
        if s.statoServizio in [StatoServizio.APPROVATO, StatoServizio.RIFIUTATO, StatoServizio.CONSEGNATO]
           and not s.is_deleted
        ]
        print(f"Servizi completati per dipendente {dipendente_id}: {[s.id for s in servizi]}")
        return servizi

    def inoltra_servizio_notaio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_LAVORAZIONE:
            print(f"Impossibile inoltrare servizio {servizio_id}: non trovato o non in lavorazione")
            return None
        print(f"Inoltro servizio {servizio_id} al notaio")
        servizio.statoServizio = StatoServizio.IN_ATTESA_APPROVAZIONE
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def servizi_da_approvare(self):
        # Ritorna tutti i servizi in stato "IN_ATTESA_APPROVAZIONE"
        return self.db.query(Servizio).filter(Servizio.statoServizio == StatoServizio.IN_ATTESA_APPROVAZIONE).all()

    def approva_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_ATTESA_APPROVAZIONE:
            print(f"Impossibile approvare servizio {servizio_id}: non trovato o non in attesa approvazione")
            return None
        print(f"Approvazione servizio {servizio_id}")
        servizio.statoServizio = StatoServizio.APPROVATO
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def rifiuta_servizio(self, servizio_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or servizio.statoServizio != StatoServizio.IN_ATTESA_APPROVAZIONE:
            print(f"Impossibile rifiutare servizio {servizio_id}: non trovato o non in attesa approvazione")
            return None
        print(f"Rifiuto servizio {servizio_id}")
        servizio.statoServizio = StatoServizio.RIFIUTATO
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def assegna_servizio(self, servizio_id: int, dipendente_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        dipendente = self.db.get(DipendenteTecnico, dipendente_id)
        if not servizio or not dipendente:
            print(f"Assegnazione fallita: servizio {servizio_id} o dipendente {dipendente_id} non trovato")
            return False
        if dipendente not in servizio.dipendenti:
            print(f"Assegno dipendente {dipendente_id} a servizio {servizio_id}")
            servizio.dipendenti.append(dipendente)
        self.db.commit()
        self.db.refresh(servizio)
        return True

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
        if filename:
            doc.filename = filename
        if path:
            doc.path = path
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # --- Associazioni e altro ---
    def aggiungi_dipendente_al_servizio(self, servizio_id: int, dipendente_id: int):
        servizio = self.db.get(Servizio, servizio_id)
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not servizio or not dip:
            print(f"Impossibile aggiungere dipendente {dipendente_id} a servizio {servizio_id}: dati mancanti")
            return False
        servizio.dipendenti.append(dip)
        self.db.commit()
        return True

    def visualizza_lavoro_da_svolgere(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            print(f"Dipendente {dipendente_id} non trovato per lavoro da svolgere")
            return []
        # Mostra solo i servizi in stato "CREATO"
        servizi = [
            s for s in dip.servizi
            if s.statoServizio == StatoServizio.CREATO and s.id not in self._servizi_virtualmente_eliminati
        ]
        print(f"Servizi da svolgere per dipendente {dipendente_id}: {[s.id for s in servizi]}")
        return servizi

    def visualizza_servizi_inizializzati(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            print(f"Dipendente {dipendente_id} non trovato per servizi inizializzati")
            return []
        # Mostra solo i servizi in stato "IN_LAVORAZIONE"
        servizi = [
            s for s in dip.servizi
            if s.statoServizio == StatoServizio.IN_LAVORAZIONE and s.id not in self._servizi_virtualmente_eliminati
        ]
        print(f"Servizi in lavorazione per dipendente {dipendente_id}: {[s.id for s in servizi]}")
        return servizi

    # --- Placeholder per invio credenziali ---
    def invia_credenziali(self, dipendente_id: int):
        dip = self.db.get(DipendenteTecnico, dipendente_id)
        if not dip:
            print(f"Dipendente {dipendente_id} non trovato per invio credenziali")
            return False
        # Qui andrebbe la logica di invio email con le credenziali
        print(f"Invio credenziali a dipendente {dipendente_id}")
        return True

    # --- Modifica documentazione generica ---
    def modifica_documentazione_per_servizio(
            self, doc_id: int, nuova_descrizione: str = None,
            nuovo_tipo=None, nuovo_filename=None
    ):
        doc = self.db.get(Documentazione, doc_id)
        if not doc:
            print(f"Documentazione {doc_id} non trovata per modifica")
            return None
        if nuova_descrizione:
            doc.descrizione = nuova_descrizione
        if nuovo_tipo:
            doc.tipo = nuovo_tipo
        if nuovo_filename:
            doc.filename = nuovo_filename
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        print(f"Modificata documentazione {doc_id}")
        return doc

    def visualizza_servizi_cliente(self, cliente_id: int):
        # Ritorna tutti i servizi per uno specifico cliente (escludendo i soft-deleted)
        servizi = [
            s for s in self.db.query(Servizio).filter(Servizio.cliente_id == cliente_id).all()
            if s.id not in self._servizi_virtualmente_eliminati
        ]
        print(f"Servizi per cliente {cliente_id}: {[s.id for s in servizi]}")
        return servizi

    def modifica_servizio(self, servizio_id: int, **kwargs):
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio:
          print(f"[DEBUG] Servizio {servizio_id} non trovato per modifica")
          return None
        print(f"[DEBUG] Modifica servizio {servizio_id} con: {kwargs}")
        print(f"[DEBUG] Valori prima della modifica:")
        for key in kwargs:
         if hasattr(servizio, key):
            print(f"    {key}: {getattr(servizio, key)}")
        for key, value in kwargs.items():
         if hasattr(servizio, key) and value is not None:
            if key == "tipo":
                print(f"[DEBUG] Ricevuto tipo: '{value}' (type: {type(value)})")
                try:
                    value = TipoServizio(value)
                    print(f"[DEBUG] Converto tipo -> {value}")
                except ValueError as e:
                    print(f"[DEBUG] ERRORE: {e}")
                    continue
            print(f"[DEBUG] Setto {key} -> {value}")
            setattr(servizio, key, value)
            self.db.commit()
            self.db.refresh(servizio)
            print(f"[DEBUG] Valori dopo la modifica:")
        for key in kwargs:
          if hasattr(servizio, key):
            print(f"    {key}: {getattr(servizio, key)}")
          print(f"[DEBUG] Servizio {servizio_id} dopo modifica: {servizio}")
          return servizio