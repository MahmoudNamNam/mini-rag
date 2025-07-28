import logging
from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
from typing import Optional, List

class CoHereProvider(LLMInterface):
    def __init__(self, api_key: str,
                 default_input_max_characters: int = 1000,
                 default_output_max_tokens: int = 1000,
                 default_generation_temperature: float = 0.2):
        
        # إعداد logger مخصص بـ scope واضح
        logger_name = f"{__name__}.CoHereProvider"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.debug("Initializing CoHereProvider...")

        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        try:
            self.client = cohere.Client(self.api_key)
            self.logger.info("Cohere client initialized successfully.")
        except Exception as e:
            self.logger.error("Failed to initialize Cohere client", exc_info=True)
            raise e

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        self.logger.info(f"Generation model set to: {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        self.logger.info(f"Embedding model set to: {model_id} with size {embedding_size}")

    def process_text(self, text: str) -> str:
        return text[:self.default_input_max_characters].strip()
    
    def generate_text(self, prompt: str, chat_history: Optional[List[dict]] = None,
                    max_output_tokens: Optional[int] = None,
                    temperature: Optional[float] = None) -> str:
        """
        Generates text based on the provided prompt and chat history.
        """
        chat_history = chat_history or []

        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            raise ValueError("Cohere client is not initialized.")
        
        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            raise ValueError("Generation model ID is not set.")

        processed_prompt = self.process_text(prompt)
        max_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        temp = temperature if temperature is not None else self.default_generation_temperature

        self.logger.debug(
            f"Sending request to Cohere chat with: model={self.generation_model_id}, "
            f"max_tokens={max_tokens}, temperature={temp}, "
            f"chat_history_items={len(chat_history)}"
        )

        try:
            response = self.client.chat(
                model=self.generation_model_id,
                chat_history=chat_history,
                message=processed_prompt,
                temperature=temp,
                max_tokens=max_tokens
            )
            
            if not response or not response.text:
                self.logger.error("No response received from Cohere API.")
                raise ValueError("No response received from Cohere API.")
            
            self.logger.info("Text generation successful.")
            return response.text.strip()
        
        except Exception as e:
            self.logger.error("Text generation failed.", exc_info=True)
            raise e

       
    def embed_text(self, text: str, document_type: Optional[str] = None):
        if not self.client:
            self.logger.error("Cohere client not initialized.")
            raise ValueError("Cohere client is not initialized.")
        if not self.embedding_model_id or not self.embedding_size:
            self.logger.error("Embedding model ID or size is not set.")
            raise ValueError("Embedding model ID or size is not set.")

        input_type = CoHereEnums.DOCUMENT.value
        if document_type and document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        processed_text = self.process_text(text)
        self.logger.debug(
            f"Embedding, model={self.embedding_model_id}, input_type={input_type}, "
        )

        try:
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=[processed_text],
                input_type=input_type,
                embedding_types=["float"] 
            )

            emb_obj = response.embeddings
            if hasattr(emb_obj,"float"):
                embedding = getattr(emb_obj,"float")[0]
            elif isinstance(emb_obj, list):
                embedding = emb_obj[0]
            else:
                self.logger.error("Unexpected embedding format from API.")
                raise ValueError("Unexpected embedding response format.")

            if len(embedding) != self.embedding_size:
                self.logger.error(f"Embedding size mismatch: expected {self.embedding_size}, "
                                  f"got {len(embedding)}")
                raise ValueError("Embedding size mismatch.")

            self.logger.info("Text embedding successful.")
            return embedding
        except Exception as e:
            self.logger.error("Text embedding failed.", exc_info=True)
            raise

    def construct_prompt(self, prompt: str, role: str):
        """
        Constructs a prompt with the specified role.
        """
        self.logger.debug(f"Constructing prompt with role={role}")
        return {"role": role, "text": self.process_text(prompt)}
