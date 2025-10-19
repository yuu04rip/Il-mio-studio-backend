from sqlalchemy.orm import Session
from app.models.user import User
from app.models.notaio import Notaio
from app.core.security import hash_password, verify_password

class GestoreLogin:
    def __init__(self, db: Session):
        self.db = db
        self.utente_corrente = None

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
            print(f"DEBUG login: utente non trovato o password errata per email={email}")
            return None
        if user.ruolo.value.lower() == "notaio":
            notaio = self.db.query(Notaio).filter(Notaio.utente_id == user.id).first()
            print(f"DEBUG login: codice_notarile payload={codice_notarile} db={getattr(notaio,'codice_notarile',None)}")
            try:
                if not notaio or int(codice_notarile) != int(notaio.codice_notarile):
                    print("DEBUG login: codice notarile non corrisponde o notaio non trovato")
                    return None
            except Exception as e:
                print(f"DEBUG login: errore nel confronto codice_notarile: {e}")
                return None
        self.utente_corrente = user
        print("DEBUG: ruolo utente trovato:", user.ruolo)
        print("DEBUG: value:", getattr(user.ruolo, "value", user.ruolo))
        print(f"DEBUG login: login riuscito per email={email}, ruolo={user.ruolo.value}")
        return user

    def change_password(self, email: str, old_password: str, new_password: str, codice_notarile: int = None):
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(old_password, user.password):
            print(f"DEBUG change_password: utente non trovato o password errata per email={email}")
            return False
        if user.ruolo.value.lower() == "notaio":
            notaio = self.db.query(Notaio).filter(Notaio.utente_id == user.id).first()
            print(f"DEBUG change_password: codice_notarile payload={codice_notarile} db={getattr(notaio,'codice_notarile',None)}")
            try:
                if not notaio or int(codice_notarile) != int(notaio.codice_notarile):
                    print("DEBUG change_password: codice notarile non corrisponde o notaio non trovato")
                    return False
            except Exception as e:
                print(f"DEBUG change_password: errore nel confronto codice_notarile: {e}")
                return False
        user.password = hash_password(new_password)
        self.db.commit()
        print(f"DEBUG change_password: password cambiata per email={email}")
        return True