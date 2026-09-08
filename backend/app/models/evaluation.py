import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class EvaluationMetric(Base):
    __tablename__ = "evaluation_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analysis_history.id"), nullable=False)
    
    # Ground truth vs actual
    expected_formula = Column(String(50), nullable=True)
    actual_formula = Column(String(50), nullable=False)
    
    is_formula_correct = Column(Boolean, default=True)
    is_filter_correct = Column(Boolean, default=True)
    is_result_correct = Column(Boolean, default=True)
    
    # Performance comparison (Manual Excel vs AI System)
    manual_steps_count = Column(Integer, default=5)
    manual_time_seconds = Column(Float, default=120.0)
    ai_time_seconds = Column(Float, default=1.5)
    
    notes = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("AnalysisHistory", back_populates="evaluation")

class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="Tutup Buku")
    
    # Template configuration
    group_by_candidates = Column(JSON, default=list) # e.g. ["Nama Merek", "Kode Barang"]
    target_field_candidates = Column(JSON, default=list) # e.g. ["Jumlah Keluar", "Total Biaya"]
    operation = Column(String(50), default="SUM")
    time_filter_type = Column(String(50), default="monthly") # monthly, quarterly, yearly
    output_format = Column(String(50), default="table_summary")
    is_system_preset = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
