from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from app.db.session import Base

class Cliente(Base):
    __tablename__ = "clienti"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    utente = relationship("User", back_populates="cliente")

    documentazioni = relationship("Documentazione", back_populates="cliente", cascade="all, delete-orphan")
    servizi_richiesti = relationship("Servizio", back_populates="cliente", cascade="all, delete-orphan")
    dipendenti = relationship("DipendenteTecnico", secondary="dipendente_cliente", back_populates="clienti")