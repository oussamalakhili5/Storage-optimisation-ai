from sqlalchemy import Column, Integer, Float, String
from app.database import Base


class StorageRecord(Base):
    __tablename__ = "storage_records"

    id = Column(Integer, primary_key=True, index=True)

    # Identifiant du serveur
    server_id = Column(String, nullable=False)

    # Date de collecte
    date = Column(String, nullable=False)

    # Données de stockage
    total_storage = Column(Float, nullable=False)
    used_storage = Column(Float, nullable=False)
    free_storage = Column(Float, nullable=False)

    # Données système ajoutées pour rendre le dataset plus riche
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    read_frequency = Column(Float, nullable=False)
    write_frequency = Column(Float, nullable=False)