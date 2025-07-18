"""Multi-language code generation agent."""

from typing import Any, Dict, List

from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class MultiLanguageCodeAgent(BaseAgent):
    """Agent capable of generating code in multiple languages."""

    SUPPORTED_LANGUAGES = {
        "python": "print('Hello from Python')\n",
        "javascript": "console.log('Hello from JavaScript');\n",
    }

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code in the requested language."""
        role_prompt = self.get_role_prompt()
        language = str(inputs.get("language", "python")).lower()

        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        prompt = f"""
        {role_prompt}

        You are a coding expert. Generate {language} code based on the following inputs.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Tests:
        {inputs.get('tests', '')}
        """

        # In a real implementation this would query the LLM. Use placeholder text for now.
        try:
            code = self.generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            code = self.SUPPORTED_LANGUAGES[language]

        # Create WSDE for the generated code
        code_wsde = None
        try:
            code_wsde = self.create_wsde(
                content=code,
                content_type="code",
                metadata={"agent": self.name, "role": self.current_role, "language": language, "type": "code"},
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "code": code,
            "wsde": code_wsde,
            "agent": self.name,
            "role": self.current_role,
            "language": language,
        }

    def get_capabilities(self) -> List[str]:
        """Return the capabilities for this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [f"generate_{lang}_code" for lang in self.SUPPORTED_LANGUAGES.keys()]
        return capabilities
