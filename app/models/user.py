from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Enum
from app.db.session import Base
from app.models.enums import Role

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cognome: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    numeroTelefonico: Mapped[str] = mapped_column(String(50), nullable=True)
    ruolo: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.CLIENTE)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente = relationship("Cliente", uselist=False, back_populates="utente")
    notaio = relationship("Notaio", uselist=False, back_populates="utente")
    dipendente = relationship("DipendenteTecnico", uselist=False, back_populates="utente")