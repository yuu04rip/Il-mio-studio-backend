from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from app.db.session import Base

class Notaio(Base):
    __tablename__ = "notai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    codice_notarile: Mapped[int] = mapped_column(Integer, nullable=False)  # <-- AGGIUNGI QUESTA RIGA!
    utente = relationship("User", back_populates="notaio")