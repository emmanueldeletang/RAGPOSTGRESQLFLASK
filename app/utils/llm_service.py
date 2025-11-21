from openai import OpenAI
from config import Config

class LLMService:
    """Service for interacting with LLM"""
    
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = self.config.LLM_MODEL
        self.temperature = self.config.LLM_TEMPERATURE
        self.max_tokens = self.config.MAX_TOKENS
    
    def generate_answer(self, question: str, context: str):
        """
        Generate an answer based on question and context
        
        Args:
            question: The user's question
            context: Relevant context from documents
            
        Returns:
            Generated answer
        """
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
If the answer cannot be found in the context, say so politely.
Provide clear, concise, and accurate answers."""
        
        user_prompt = f"""Context:
{context}

Question: {question}

Please provide a clear answer based on the context above."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating answer: {e}")
            raise
