from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum, func
from app.db.session import Base
from app.models.enums import TipoDocumentazione

class Documentazione(Base):
    __tablename__ = "documentazioni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clienti.id"))
    cliente = relationship("Cliente", back_populates="documentazioni")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoDocumentazione] = mapped_column(Enum(TipoDocumentazione), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    servizi = relationship("Servizio", secondary="servizio_documentazione", back_populates="lavoroCaricato")