import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class TrainingSample(Base):
    __tablename__ = "training_samples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    formula_label = Column(String(50), nullable=False) # e.g. SUM, SUMIF, SUMIFS, XLOOKUP, etc.
    operation = Column(String(50), nullable=False)     # SUM, AVERAGE, COUNT, MAX, MIN, LOOKUP, IF, etc.
    intent = Column(String(50), default="aggregation") # aggregation, conditional_aggregation, lookup, logical, statistical
    conditions_count = Column(Integer, default=0)
    target_term = Column(String(100), nullable=True)
    is_ambiguous = Column(Boolean, default=False)
    source = Column(String(50), default="synthetic_ptpn") # synthetic_ptpn, user_feedback, expert_curated
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationQuery(Base):
    __tablename__ = "evaluation_queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    expected_formula = Column(String(50), nullable=False)
    expected_operation = Column(String(50), nullable=False)
    expected_conditions_count = Column(Integer, default=0)
    difficulty = Column(String(20), default="medium") # easy, medium, hard, ambiguous
    is_ambiguous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), nullable=False, unique=True) # e.g. formula_rf_v1
    model_name = Column(String(100), default="RandomForestClassifier + TfidfVectorizer")
    sample_count = Column(Integer, default=0)
    test_sample_count = Column(Integer, default=0)
    formula_classes_count = Column(Integer, default=18)
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    macro_f1 = Column(Float, default=0.0)
    weighted_f1 = Column(Float, default=0.0)
    confusion_matrix = Column(JSON, default=dict)
    classification_report = Column(JSON, default=dict)
    model_parameters = Column(JSON, default=dict)
    feature_configuration = Column(JSON, default=dict)
    random_state = Column(Integer, default=42)
    model_file_path = Column(String(500), nullable=False)
    vectorizer_file_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False)
    training_duration_seconds = Column(Float, default=0.0)
    trained_at = Column(DateTime, default=datetime.utcnow)

    metrics = relationship("ModelMetric", back_populates="training_run", cascade="all, delete-orphan")

class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    training_run_id = Column(String(36), ForeignKey("training_runs.id"), nullable=False)
    formula_name = Column(String(50), nullable=False)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    support = Column(Integer, default=0)

    training_run = relationship("TrainingRun", back_populates="metrics")

class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analysis_history.id"), nullable=True)
    user_query = Column(Text, nullable=False)
    predicted_formula = Column(String(50), nullable=False)
    actual_formula = Column(String(50), nullable=True)
    is_correct = Column(Boolean, default=True)
    confidence = Column(Float, default=0.0)
    user_feedback_text = Column(Text, nullable=True)
    reviewed_for_training = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_query_id = Column(String(36), ForeignKey("evaluation_queries.id"), nullable=True)
    training_run_version = Column(String(50), nullable=True)
    query_text = Column(Text, nullable=False)
    expected_formula = Column(String(50), nullable=False)
    predicted_formula = Column(String(50), nullable=False)
    final_decision_formula = Column(String(50), nullable=False)
    is_ml_correct = Column(Boolean, default=False)
    is_decision_correct = Column(Boolean, default=False)
    is_e2e_correct = Column(Boolean, default=False)
    ml_confidence = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
