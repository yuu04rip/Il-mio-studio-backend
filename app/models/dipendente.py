from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Enum, ForeignKey
from app.db.session import Base
from app.models.enums import TipoDipendenteTecnico

class DipendenteTecnico(Base):
    __tablename__ = "dipendenti_tecnici"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    tipo: Mapped[TipoDipendenteTecnico] = mapped_column(Enum(TipoDipendenteTecnico), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "dipendente_tecnico",
        "polymorphic_on": tipo,
    }

    # Relazioni comuni
    clienti = relationship("Cliente", secondary="dipendente_cliente", back_populates="dipendenti")
    servizi = relationship("Servizio", secondary="dipendente_servizio", back_populates="dipendenti")
    utente = relationship("User", back_populates="dipendente", overlaps="notaio")

# Sottoclasse per il tipo "contabile"
class Contabile(DipendenteTecnico):
    __mapper_args__ = {
        "polymorphic_identity": "contabile",
    }

# Sottoclasse per il tipo "assistente"
class Assistente(DipendenteTecnico):
    __mapper_args__ = {
        "polymorphic_identity": "assistente",
    }