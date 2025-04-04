from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from app.product_tool import ProductTool
from app.faq_tool import FAQTool

class ProductAssistantAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-4", temperature=0)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize tools
        self.product_tool = ProductTool()
        self.faq_tool = FAQTool(api_key=api_key)
        
        # Initialize agent with a better system message
        system_message = """You are a helpful AI assistant for an e-commerce store.
        You can answer questions about products and general customer service inquiries.
        For product-related questions, use the product_query_tool.
        For general questions about shipping, returns, payment, etc., use the faq_query_tool.
        Always provide accurate information based on the data available to you.
        If you don't know the answer, admit it rather than making up information."""
        
        self.agent = initialize_agent(
            tools=[self.product_tool, self.faq_tool],
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            agent_kwargs={"system_message": system_message}
        )
    
    def process_query(self, query: str) -> str:
        """Process user query and return response."""
        try:
            # Determine query type for better routing
            query_type = self._classify_query(query.lower())
            
            # Route to appropriate tool based on query type
            if query_type == "faq":
                return self.faq_tool._run(query)
            elif query_type == "product":
                return self.product_tool._run(query)
            else:
                # Use the agent for complex or ambiguous queries
                response = self.agent.run(input=query)
                return response
        except Exception as e:
            return f"I apologize, but I encountered an error processing your query. Please try rephrasing your question or ask something else."
    
    def _classify_query(self, query: str) -> str:
        """Classify the query as product-related, FAQ-related, or ambiguous."""
        # FAQ-related keywords
        faq_keywords = [
            "return policy", "shipping policy", "warranty", "payment methods", 
            "track order", "delivery time", "discount", "bulk order", "international shipping",
            "refund", "cancel order", "contact", "support"
        ]
        
        # Product-related keywords
        product_keywords = [
            "product", "price", "stock", "available", "electronics", "laptop", 
            "smartwatch", "accessories", "computer", "wearable", "rating", "top rated",
            "best", "cheapest", "under", "less than", "how much", "features"
        ]
        
        # Count matches for each category
        faq_count = sum(1 for keyword in faq_keywords if keyword in query)
        product_count = sum(1 for keyword in product_keywords if keyword in query)
        
        # Determine query type based on keyword matches
        if faq_count > product_count:
            return "faq"
        elif product_count > faq_count:
            return "product"
        else:
            return "ambiguous" 