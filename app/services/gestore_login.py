from sqlalchemy.orm import Session
from app.models.user import User
from app.models.notaio import Notaio
from app.core.security import hash_password, verify_password

class GestoreLogin:
    def __init__(self, db: Session):
        self.db = db
        self.utente_corrente = None  # opzionale, utile se vuoi salvare chi ha fatto login

    # Lista utenti
    def lista_utenti(self):
        return self.db.query(User).all()

    def aggiungi_utente(self, user: User):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str, codice_notarile: int = None):
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password):
            return None
        if user.ruolo.value == "notaio":
            notaio = self.db.query(Notaio).filter(Notaio.utente_id == user.id).first()
            if not notaio or codice_notarile != notaio.codice_notarile:
                return None
        self.utente_corrente = user
        return user

    def change_password(self, email: str, old_password: str, new_password: str, codice_notarile: int = None):
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(old_password, user.password):
            return False
        if user.ruolo.value == "notaio":
            notaio = self.db.query(Notaio).filter(Notaio.utente_id == user.id).first()
            if not notaio or codice_notarile != notaio.codice_notarile:
                return False
        user.password = hash_password(new_password)
        self.db.commit()
        return True