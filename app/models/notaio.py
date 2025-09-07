from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from app.db.session import Base
from app.models.dipendente import DipendenteTecnico

class Notaio(DipendenteTecnico):
    __tablename__ = "notai"

    id: Mapped[int] = mapped_column(ForeignKey("dipendenti_tecnici.id"), primary_key=True)
    codice_notarile: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    utente = relationship("User", back_populates="notaio", overlaps="dipendente")

    __mapper_args__ = {
        "polymorphic_identity": "notaio",
    }