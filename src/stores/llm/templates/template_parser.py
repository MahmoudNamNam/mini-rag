import os
import importlib
import logging
from string import Template
from typing import Optional


class TemplateParser:
    def __init__(self, language: Optional[str] = None, default_language: str = "en"):
        self.logger = logging.getLogger(__name__)
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = default_language

        self.set_language(language)

    def set_language(self, language: Optional[str]):
        if not language:
            self.logger.debug("No language provided. Using default: '%s'", self.default_language)
            self.language = self.default_language
            return

        language_path = os.path.join(self.current_path, "locales", language)
        if os.path.exists(language_path):
            self.logger.info("Using language: '%s'", language)
            self.language = language
        else:
            self.logger.warning("Language folder '%s' not found. Falling back to default: '%s'",
                                language, self.default_language)
            self.language = self.default_language

    def get(self, group: str, key: str, vars: Optional[dict] = None) -> Optional[str]:
        if not group or not key:
            self.logger.warning("Template group or key not provided.")
            return None

        vars = vars or {}
        languages_to_try = [self.language, self.default_language]

        for lang in languages_to_try:
            try:
                module_path = f"stores.llm.templates.locales.{lang}.{group}"
                self.logger.debug("Trying template: %s (key='%s')", module_path, key)
                module = importlib.import_module(module_path)

                template_obj = getattr(module, key, None)
                if template_obj and isinstance(template_obj, Template):
                    self.logger.debug("Template found: '%s.%s' [%s]", group, key, lang)
                    return template_obj.substitute(vars)

                self.logger.warning("Key '%s' not found in template group '%s' [%s]", key, group, lang)

            except ModuleNotFoundError:
                self.logger.warning("Template group module '%s' not found for language '%s'", group, lang)
            except Exception as e:
                self.logger.error("Failed to load or render template '%s.%s' [%s]: %s",
                                  group, key, lang, e, exc_info=True)

        self.logger.error("Template '%s.%s' not found in any available language.", group, key)
        return None
