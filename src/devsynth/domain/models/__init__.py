from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Import wsde_summarization to ensure the WSDETeam class is patched with summarization methods
import devsynth.domain.models.wsde_summarization

