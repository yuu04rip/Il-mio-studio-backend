from app.models.services import Servizio
from sqlalchemy.orm import Session
from typing import List, Optional

class GestoreBackup:
    def __init__(self, db: Session):
        self.db = db

    def setup_backup(self):
        """
        Logica di setup/inizializzazione backup.
        Puoi usarla per creare strutture, loggare, ecc.
        """
        # implementa setup reale se serve (es. connessione a storage esterno)
        print("GestoreBackup inizializzato!")

    def servizi_archiviati(self) -> List[Servizio]:
        """
        Restituisce la lista di tutti i servizi archiviati (archived == True).
        """
        return self.db.query(Servizio).filter(Servizio.archived == True, Servizio.is_deleted == False).all()

    def mostra_servizi_archiviati(self) -> List[Servizio]:
        """
        Alias per servizi_archiviati(), per chiarezza UML.
        """
        return self.servizi_archiviati()

    def archivia_servizio(self, servizio: Servizio) -> Servizio:
        """
        Archivia un servizio (imposta archived a True).
        """
        if getattr(servizio, "archived", False):
            # già archiviato
            return servizio
        servizio.archived = True
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def dearchivia_servizio(self, servizio: Servizio) -> Servizio:
        """
        Rende di nuovo attivo un servizio archiviato (imposta archived a False).
        """
        if not getattr(servizio, "archived", False):
            # già attivo
            return servizio
        servizio.archived = False
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def modifica_servizio_archiviato(self, servizio: Servizio, archived: bool) -> Servizio:
        """
        Cambia lo stato di archiviazione di un servizio.
        archived: bool -> True per archiviare, False per dearchiviare
        """
        servizio.archived = bool(archived)
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def elimina_servizio_archiviato(self, servizio_id: int) -> bool:
        """
        Elimina definitivamente un servizio archiviato.
        """
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or not getattr(servizio, "archived", False):
            return False
        self.db.delete(servizio)
        self.db.commit()
        return True

    def get_servizio_archiviato(self, servizio_id: int) -> Optional[Servizio]:
        """
        Restituisce un singolo servizio archiviato dato il suo id.
        """
        servizio = self.db.get(Servizio, servizio_id)
        if servizio and getattr(servizio, "archived", False):
            return servizio
        return None