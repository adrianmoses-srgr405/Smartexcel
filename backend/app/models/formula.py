import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, JSON
from app.core.database import Base

class FormulaKnowledge(Base):
    __tablename__ = "formula_knowledge"

    id = Column(String(50), primary_key=True) # e.g. SUMIFS, XLOOKUP
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False) # Aggregation, Lookup, Statistical, Logical
    keywords = Column(JSON, default=list)
    description = Column(Text, nullable=False)
    syntax_template = Column(String(255), nullable=False)
    required_parameters = Column(JSON, default=list)
    compatible_data_types = Column(JSON, default=list)
    min_filters = Column(Integer, default=0)
    max_filters = Column(Integer, default=99)
    use_cases = Column(JSON, default=list)
    examples = Column(JSON, default=list)
    explanation_template = Column(Text, nullable=False)
    validation_rules = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
