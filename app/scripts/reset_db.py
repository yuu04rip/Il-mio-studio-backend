from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+mysqlconnector://pythonuser:python123@utenti.ctisa2uy4kry.eu-central-1.rds.amazonaws.com:3306/utenti"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
    conn.execute(text("TRUNCATE TABLE notai;"))
    conn.execute(text("TRUNCATE TABLE dipendenti_tecnici;"))
    conn.execute(text("TRUNCATE TABLE clienti;"))
    conn.execute(text("TRUNCATE TABLE users;"))
    # Aggiungi altri truncate se hai altre tabelle
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
print("Tutte le tabelle sono state azzerate!")