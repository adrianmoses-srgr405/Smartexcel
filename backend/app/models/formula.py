import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class FormulaKnowledge(Base):
    __tablename__ = "formula_knowledge"

    id = Column(String(50), primary_key=True) # e.g. SUM, SUMIF, SUMIFS, XLOOKUP
    formula_name = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False) # Aggregation, Conditional Aggregation, Statistical, Lookup, Logical, Counting
    keywords = Column(JSON, default=list)
    description = Column(Text, nullable=False)
    use_case = Column(Text, nullable=False)
    syntax_template = Column(String(255), nullable=False)
    parameter_definition = Column(JSON, default=dict)
    required_parameters = Column(JSON, default=list)
    compatible_data_types = Column(JSON, default=list)
    required_conditions = Column(Integer, default=0)
    min_conditions = Column(Integer, default=0)
    max_conditions = Column(Integer, default=99)
    min_filters = Column(Integer, default=0)
    max_filters = Column(Integer, default=99)
    use_cases = Column(JSON, default=list)
    examples = Column(JSON, default=list)
    explanation_template = Column(Text, nullable=False)
    validation_rules = Column(JSON, default=list)
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    example_items = relationship("FormulaExample", back_populates="formula", cascade="all, delete-orphan")

class FormulaExample(Base):
    __tablename__ = "formula_examples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    formula_id = Column(String(50), ForeignKey("formula_knowledge.id"), nullable=False)
    example_query = Column(Text, nullable=False)
    example_formula = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    formula = relationship("FormulaKnowledge", back_populates="example_items")
