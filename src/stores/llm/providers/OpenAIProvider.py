import logging
from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
from typing import Optional, List


class OpenAIProvider(LLMInterface):
    def __init__(self, api_key: str, api_url: str = None,
                 default_input_max_characters: int = 1000,
                 default_output_max_tokens: int = 1000,
                 default_generation_temperature: float = 0.2):
        
        logger_name = f"{__name__}.OpenAIProvider.{api_url or 'default'}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.debug("Initializing OpenAIProvider...")

        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.enums = OpenAIEnums

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )
            self.logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            self.logger.error("Failed to initialize OpenAI client", exc_info=True)
            raise e

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        self.logger.info(f"Generation model set to: {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        self.logger.info(f"Embedding model set to: {model_id} with size {embedding_size}")


    def generate_text(self, prompt: str, chat_history: Optional[List[dict]] = None,
                    max_output_tokens: Optional[int] = None,
                    temperature: Optional[float] = None) -> str:
        """
        Generates a chat completion using OpenAI's chat model.

        Args:
            prompt: The user prompt to generate a response for.
            chat_history: Optional list of prior messages for context.
            max_output_tokens: Optional override for token output limit.
            temperature: Optional override for generation randomness.

        Returns:
            The generated response text.
        """
        
        chat_history = chat_history or []

        
        if not self.client:
            self.logger.error("OpenAI client was not initialized.")
            raise RuntimeError("OpenAI client is not initialized.")
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            raise RuntimeError("Generation model ID is not set.")
        
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        temperature = temperature if temperature is not None else self.default_generation_temperature

        self.logger.debug(
            f"Generating text with model: {self.generation_model_id}, Max tokens: {max_output_tokens}, Temperature: {temperature}"
        )

        chat_history.append(self.construct_prompt(prompt= prompt,role= OpenAIEnums.USER.value))
        try:
            response = self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature
            )

            try:
                message = response.choices[0].message
                content = getattr(message, 'content', None)
                if not content:
                    self.logger.error("No content in response message.")
                    raise ValueError("No content in response message.")
                self.logger.info("Text generation successful.")
                return content
            except (IndexError, AttributeError) as e:
                self.logger.error("Malformed response structure.", exc_info=True)
                raise ValueError("Chat completion response was malformed.") from e

        except Exception as e:
            self.logger.error("Text generation failed", exc_info=True)
            raise

    
    def process_text(self, text: str) -> str:
        return text[:self.default_input_max_characters].strip()




    def embed_text(self, text: str, document_type: str = None) -> Optional[List[float]]:
        if not self.client:
            self.logger.error("OpenAI client was not initialized.")
            raise RuntimeError("OpenAI client is not initialized.")
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set.")
            raise RuntimeError("Embedding model ID is not set.")

        try:
            self.logger.debug(f"Embedding text with model: {self.embedding_model_id}, doc_type: {document_type}")
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model_id
            )

            embedding_data = getattr(response, 'data', [None])[0]
            if not embedding_data or not getattr(embedding_data, 'embedding', None):
                self.logger.error("No embedding data returned.")
                raise ValueError("Embedding response did not contain valid data.")

            self.logger.info("Text embedding successful.")
            return embedding_data.embedding

        except Exception as e:
            self.logger.error("Text embedding failed", exc_info=True)
            raise

    def construct_prompt(self, prompt: str, role: str):
        self.logger.debug(f"Constructing prompt with role={role}")
        return {"role": role, "content": self.process_text(prompt)}
