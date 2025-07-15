"""
Compatibility layer for AI Team Support.
This module provides backward compatibility for existing imports.
"""

# Import core components from new locations
from core import *
from src.config.settings import *
from plugins import *

# Re-export commonly used components
from src.core.models import *
from src.core.services import *
from src.core.ai import *
from src.core.agents import *
from src.core.adapters import *
from src.core.security import *
from src.core.knowledge import *
from src.core.chat import *
from src.core.logging import *
from src.core.exceptions import * 