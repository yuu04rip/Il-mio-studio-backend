from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger
from app.db.session import Base  # usa il Base del progetto

class ClienteCounters(Base):
    __tablename__ = "cliente_counters"

    cliente_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)