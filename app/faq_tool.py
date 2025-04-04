from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, ClassVar, Type, Any, Tuple
import pandas as pd
from app.data_loader import load_faq_data
from langchain_openai import ChatOpenAI

class FAQQueryInput(BaseModel):
    query: str = Field(description="The natural language query about company policies, shipping, returns, etc.")

class FAQTool(BaseTool):
    name: ClassVar[str] = "faq_query_tool"
    description: ClassVar[str] = """
    Use this tool when the user is asking general questions about shipping, returns, 
    payment methods, warranties, delivery times, discounts, or other customer service related questions.
    """
    args_schema: ClassVar[Type[BaseModel]] = FAQQueryInput
    
    # Define instance attributes as model fields
    faq_df: Optional[pd.DataFrame] = None
    llm: Optional[Any] = None
    
    def __init__(self, api_key: str, **data):
        super().__init__(**data)
        self.faq_df = load_faq_data()
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-4")
    
    def _run(self, query: str) -> str:
        """Process FAQ-related queries."""
        # First try direct keyword matching for common queries
        query_lower = query.lower()
        
        # Direct matching for common queries
        direct_match = self._direct_keyword_match(query_lower)
        if direct_match:
            return direct_match
        
        # If no direct match, use semantic matching with LLM
        return self._semantic_match(query)
    
    def _direct_keyword_match(self, query_lower: str) -> Optional[str]:
        """Match query using direct keyword matching."""
        keyword_mappings = {
            "return policy": ["return", "policy", "send back", "refund"],
            "international shipping": ["international", "shipping", "ship", "abroad", "overseas"],
            "track order": ["track", "order", "package", "delivery status"],
            "payment methods": ["payment", "pay", "credit card", "debit card", "paypal"],
            "warranty": ["warranty", "guarantee", "repair"],
            "delivery time": ["delivery", "shipping time", "arrive", "how long"],
            "bulk orders": ["bulk", "discount", "wholesale", "large order"]
        }
        
        # Check each FAQ topic
        for topic, keywords in keyword_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                for _, row in self.faq_df.iterrows():
                    if any(keyword in row["Question"].lower() for keyword in keywords):
                        return row["Answer"]
        
        return None
    
    def _semantic_match(self, query: str) -> str:
        """Match query using semantic similarity via LLM."""
        prompt = f"""
        Given the following FAQs and a user question, find the most relevant FAQ and return its answer.
        If none of the FAQs are relevant, say "I don't have information about that specific question."

        FAQs:
        {self.faq_df.to_string(index=False)}

        User Question: {query}

        The most relevant answer is:
        """
        
        response = self.llm.invoke(prompt)
        return response.content 