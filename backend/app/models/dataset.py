import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    dataset_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    analyses = relationship("AnalysisHistory", back_populates="dataset", cascade="all, delete-orphan")

class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    sanitized_name = Column(String(255), nullable=False)
    column_index = Column(Integer, nullable=False)
    excel_column_letter = Column(String(10), nullable=False)  # A, B, C, etc.
    inferred_type = Column(String(50), nullable=False)       # Numeric, Date, Categorical, Text, Boolean
    null_count = Column(Integer, default=0)
    unique_count = Column(Integer, default=0)
    min_value = Column(String(255), nullable=True)
    max_value = Column(String(255), nullable=True)
    mean_value = Column(String(255), nullable=True)
    sample_values = Column(JSON, default=list)

    dataset = relationship("Dataset", back_populates="columns")
