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
        print("GestoreBackup inizializzato!")

    def servizi_archiviati(self) -> List[Servizio]:
        """
        Restituisce la lista di tutti i servizi archiviati (statoServizio==True).
        """
        return self.db.query(Servizio).filter(Servizio.statoServizio == True).all()

    def mostra_servizi_archiviati(self) -> List[Servizio]:
        """
        Alias per servizi_archiviati(), per chiarezza UML.
        """
        return self.servizi_archiviati()

    def archivia_servizio(self, servizio: Servizio) -> Servizio:
        """
        Archivia un servizio (imposta statoServizio a True).
        """
        if servizio.statoServizio:
            # Già archiviato
            return servizio
        servizio.statoServizio = True
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def dearchivia_servizio(self, servizio: Servizio) -> Servizio:
        """
        Rende di nuovo attivo un servizio archiviato (imposta statoServizio a False).
        """
        if not servizio.statoServizio:
            # Già attivo
            return servizio
        servizio.statoServizio = False
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def modifica_servizio_archiviato(self, servizio: Servizio, statoServizio: bool) -> Servizio:
        """
        Cambia lo stato di archiviazione di un servizio.
        """
        servizio.statoServizio = statoServizio
        self.db.add(servizio)
        self.db.commit()
        self.db.refresh(servizio)
        return servizio

    def elimina_servizio_archiviato(self, servizio_id: int) -> bool:
        """
        Elimina definitivamente un servizio archiviato.
        """
        servizio = self.db.get(Servizio, servizio_id)
        if not servizio or not servizio.statoServizio:
            return False
        self.db.delete(servizio)
        self.db.commit()
        return True

    def get_servizio_archiviato(self, servizio_id: int) -> Optional[Servizio]:
        """
        Restituisce un singolo servizio archiviato dato il suo id.
        """
        servizio = self.db.get(Servizio, servizio_id)
        if servizio and servizio.statoServizio:
            return servizio
        return None