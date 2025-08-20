from sqlalchemy import Table, Column, ForeignKey, Integer
from app.db.session import Base

dipendente_cliente = Table(
    "dipendente_cliente",
    Base.metadata,
    Column("dipendente_id", Integer, ForeignKey("dipendenti_tecnici.id")),
    Column("cliente_id", Integer, ForeignKey("clienti.id"))
)

servizio_documentazione = Table(
    "servizio_documentazione",
    Base.metadata,
    Column("servizio_id", Integer, ForeignKey("servizi.id")),
    Column("documentazione_id", Integer, ForeignKey("documentazioni.id"))
)

dipendente_servizio = Table(
    "dipendente_servizio",
    Base.metadata,
    Column("dipendente_id", Integer, ForeignKey("dipendenti_tecnici.id")),
    Column("servizio_id", Integer, ForeignKey("servizi.id"))
)