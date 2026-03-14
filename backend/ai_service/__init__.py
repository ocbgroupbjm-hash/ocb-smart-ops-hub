# OCB TITAN ERP - AI Service Package
# =====================================

from .data_access import (
    AIDataAccessLayer,
    AIFeatureBuilder,
    AIKillSwitch,
    AIEngineDisabledException,
    AIReadOnlyViolationException,
    get_ai_config,
    is_ai_enabled
)

from .insights_engine import AIInsightsEngine
from .decision_logger import AIDecisionLogger
from .rbac_gateway import AIRBACGateway, AI_ALLOWED_ROLES

__all__ = [
    "AIDataAccessLayer",
    "AIFeatureBuilder",
    "AIInsightsEngine",
    "AIDecisionLogger",
    "AIRBACGateway",
    "AIKillSwitch",
    "AIEngineDisabledException",
    "AIReadOnlyViolationException",
    "AI_ALLOWED_ROLES",
    "get_ai_config",
    "is_ai_enabled"
]

__version__ = "1.0.0"
