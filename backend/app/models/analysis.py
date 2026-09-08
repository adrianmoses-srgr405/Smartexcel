import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    user_query = Column(Text, nullable=False)
    
    # AI Structured Intent
    parsed_intent = Column(JSON, default=dict)
    
    # Formula Decision Engine Results
    selected_formula_id = Column(String(50), nullable=False)
    generated_excel_formula = Column(Text, nullable=False)
    formula_explanation = Column(Text, nullable=False)
    
    # Execution & Results
    calculation_results = Column(JSON, default=dict)
    result_summary = Column(Text, nullable=True)
    execution_time_ms = Column(Float, default=0.0)
    
    # Export path if exported
    export_file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="analyses")
    evaluation = relationship("EvaluationMetric", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
