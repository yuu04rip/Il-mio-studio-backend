from sqlalchemy import Enum, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.session import Base
from app.models.enums import TipoServizio, StatoServizio
from app.models.tables import dipendente_servizio

class Servizio(Base):
    __tablename__ = "servizi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clienti.id"), nullable=False)
    cliente = relationship("Cliente", back_populates="servizi_richiesti")

    codiceCorrente: Mapped[int] = mapped_column(Integer)
    codiceServizio: Mapped[int] = mapped_column(Integer)
    dataConsegna: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dataRichiesta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    statoServizio: Mapped[StatoServizio] = mapped_column(Enum(StatoServizio), default=StatoServizio.CREATO, nullable=False)
    tipo: Mapped[TipoServizio] = mapped_column(Enum(TipoServizio), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # RELAZIONE MOLTI-A-MOLTI!
    dipendenti = relationship("DipendenteTecnico", secondary=dipendente_servizio, back_populates="servizi")
    lavoroCaricato = relationship("Documentazione", secondary="servizio_documentazione", back_populates="servizi")