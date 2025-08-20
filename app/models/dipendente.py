from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Enum, ForeignKey
from app.db.session import Base
from app.models.enums import TipoDipendenteTecnico

class DipendenteTecnico(Base):
    __tablename__ = "dipendenti_tecnici"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    utente = relationship("User", back_populates="dipendente")
    tipo: Mapped[TipoDipendenteTecnico] = mapped_column(Enum(TipoDipendenteTecnico), nullable=False)

    clienti = relationship("Cliente", secondary="dipendente_cliente", back_populates="dipendenti")
    servizi = relationship("Servizio", secondary="dipendente_servizio", back_populates="dipendenti")