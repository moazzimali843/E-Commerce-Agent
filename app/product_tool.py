from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, ClassVar, Type, Annotated
import pandas as pd
import re
from app.data_loader import (
    load_product_data,
    filter_products,
    get_product_details,
    get_top_products
)

class ProductQueryInput(BaseModel):
    query: str = Field(description="The natural language query about products")

class ProductTool(BaseTool):
    name: ClassVar[str] = "product_query_tool"
    description: ClassVar[str] = """
    Use this tool when the user is asking about products, prices, categories, ratings, 
    stock levels, or any other product-related information.
    """
    args_schema: ClassVar[Type[BaseModel]] = ProductQueryInput
    
    # Define product_df as a class variable with default None
    product_df: Optional[pd.DataFrame] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load the product data in __init__
        self.product_df = load_product_data()
        # Print column names for debugging
        print(f"Available columns: {self.product_df.columns.tolist()}")
    
    def _run(self, query: str) -> str:
        """Process product-related queries."""
        # Check if product data is loaded
        if self.product_df is None or self.product_df.empty:
            return "I'm sorry, but I couldn't access the product database."
            
        query_lower = query.lower()
        
        # Special handling for mobile/phone queries
        if "mobile" in query_lower or "phone" in query_lower:
            try:
                # Try to find products in Electronics or similar category
                filtered = self._filter_by_category_keyword(["mobile", "phone", "smartphone", "cell"])
                
                # Apply price filter if present
                price_match = re.search(r'under\s+\$?(\d+)', query_lower) or re.search(r'less than\s+\$?(\d+)', query_lower)
                if price_match:
                    max_price = float(price_match.group(1))
                    filtered = filtered[filtered['Price'] <= max_price]
                
                if filtered.empty:
                    return "I couldn't find any mobile phones matching your criteria."
                
                return "Mobile Phone Products:\n\n" + "\n\n".join(
                    [self._format_product(p) for p in filtered.to_dict('records')]
                )
            except Exception as e:
                print(f"Error in mobile query: {str(e)}")
                return f"I'm having trouble finding mobile phones. Please try a different query."
        
        # Handle complex natural language queries with multiple filters
        if self._is_complex_query(query_lower):
            return self._handle_complex_query(query_lower)
        
        # Handle specific product queries like "laptop pro"
        for product_name in self.product_df['Product_Name'].values:
            if product_name.lower() in query_lower:
                details = get_product_details(self.product_df, product_name=product_name)
                if details:
                    return f"Product Details:\n{self._format_product(details)}"
        
        # Handle simple product category queries
        if "smartwatch" in query_lower or "smartwatches" in query_lower:
            try:
                filtered = self._filter_by_category_keyword(["smartwatch", "wearable", "watch"])
                if not filtered.empty:
                    return "Smartwatch Products:\n\n" + "\n\n".join(
                        [self._format_product(p) for p in filtered.to_dict('records')]
                    )
                else:
                    return "I couldn't find any smartwatches in our inventory."
            except Exception as e:
                print(f"Error in smartwatch query: {str(e)}")
                return f"I'm having trouble finding smartwatch information. Please try a different query."
        
        # Handle laptop queries
        if "laptop" in query_lower or "computer" in query_lower:
            try:
                filtered = self._filter_by_category_keyword(["laptop", "computer", "notebook"])
                if not filtered.empty:
                    return "Laptop Products:\n\n" + "\n\n".join(
                        [self._format_product(p) for p in filtered.to_dict('records')]
                    )
                else:
                    return "I couldn't find any laptops in our inventory."
            except Exception as e:
                print(f"Error in laptop query: {str(e)}")
                return f"I'm having trouble finding laptop information. Please try a different query."
        
        # Handle price range queries
        if "under" in query_lower or "less than" in query_lower or "cheaper than" in query_lower:
            try:
                price_match = re.search(r'under\s+\$?(\d+)', query_lower) or re.search(r'less than\s+\$?(\d+)', query_lower)
                if price_match:
                    max_price = float(price_match.group(1))
                    
                    # Try to extract category from query
                    category_keywords = {
                        "electronics": ["electronics", "gadget", "device"],
                        "computer": ["laptop", "computer", "notebook"],
                        "wearable": ["smartwatch", "wearable", "watch"],
                        "mobile": ["mobile", "phone", "smartphone", "cell"],
                        "accessory": ["accessory", "accessories", "headphone", "earphone"]
                    }
                    
                    filtered_df = self.product_df.copy()
                    
                    # Apply category filter if present in query
                    for category, keywords in category_keywords.items():
                        if any(keyword in query_lower for keyword in keywords):
                            filtered_df = self._filter_by_category_keyword(keywords, df=filtered_df)
                            break
                    
                    # Apply price filter
                    filtered_df = filtered_df[filtered_df['Price'] <= max_price]
                    
                    if filtered_df.empty:
                        return f"No products found under ${max_price}."
                    
                    category_text = ""
                    for cat, keywords in category_keywords.items():
                        if any(keyword in query_lower for keyword in keywords):
                            category_text = f" in {cat}"
                            break
                    
                    return f"Products{category_text} under ${max_price}:\n\n" + "\n\n".join(
                        [self._format_product(p) for p in filtered_df.to_dict('records')]
                    )
            except Exception as e:
                print(f"Error in price range query: {str(e)}")
                return "I'm having trouble finding products in that price range. Please try a different query."
        
        # Default: return all products
        try:
            return "Available Products:\n\n" + "\n\n".join(
                [self._format_product(p) for p in self.product_df.head(5).to_dict('records')]
            )
        except Exception as e:
            print(f"Error in default response: {str(e)}")
            return "I'm having trouble retrieving product information. Please try a more specific query."
    
    def _filter_by_category_keyword(self, keywords: List[str], df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Filter products by category keywords, handling potential column name variations."""
        if df is None:
            df = self.product_df.copy()
        
        # Try different possible column names for category
        category_columns = ['Category', 'category', 'product_category', 'ProductCategory', 'product_type', 'ProductType']
        
        for col in category_columns:
            if col in df.columns:
                mask = df[col].astype(str).str.lower().apply(
                    lambda x: any(keyword in x.lower() for keyword in keywords)
                )
                filtered = df[mask]
                if not filtered.empty:
                    return filtered
        
        # If no exact match found, try partial string matching on all columns
        result = pd.DataFrame()
        for keyword in keywords:
            for col in df.columns:
                try:
                    if df[col].dtype == object:  # Only check string columns
                        matches = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]
                        result = pd.concat([result, matches])
                except:
                    continue
        
        return result.drop_duplicates()
    
    def _is_complex_query(self, query: str) -> bool:
        """Check if the query contains multiple filter conditions."""
        # Count the number of filter keywords in the query
        filter_keywords = ['under', 'less than', 'top', 'best', 'rated', 'in stock', 'available', 'category']
        count = sum(1 for keyword in filter_keywords if keyword in query)
        return count >= 2
    
    def _handle_complex_query(self, query: str) -> str:
        """Handle complex queries with multiple filters."""
        try:
            # Initialize filter parameters
            category_keywords = []
            min_price = None
            max_price = None
            min_rating = None
            min_stock = None
            
            # Extract category keywords
            if "smartwatch" in query or "wearable" in query or "watch" in query:
                category_keywords.extend(["smartwatch", "wearable", "watch"])
            if "laptop" in query or "computer" in query or "notebook" in query:
                category_keywords.extend(["laptop", "computer", "notebook"])
            if "phone" in query or "mobile" in query or "smartphone" in query:
                category_keywords.extend(["phone", "mobile", "smartphone"])
            if "accessory" in query or "accessories" in query:
                category_keywords.extend(["accessory", "accessories"])
            if "electronics" in query or "gadget" in query:
                category_keywords.extend(["electronics", "gadget"])
            
            # Extract price range
            price_match = re.search(r'under\s+\$?(\d+)', query) or re.search(r'less than\s+\$?(\d+)', query)
            if price_match:
                max_price = float(price_match.group(1))
            
            # Extract rating requirement
            if "top" in query or "best" in query or "highest rated" in query or "top rated" in query:
                min_rating = 4.0  # Consider 4+ as top rated
            
            # Extract stock requirement
            if "in stock" in query or "available" in query:
                min_stock = 1
            
            # Start with all products
            filtered_df = self.product_df.copy()
            
            # Apply category filter if keywords found
            if category_keywords:
                filtered_df = self._filter_by_category_keyword(category_keywords, filtered_df)
            
            # Apply price filter if specified
            if max_price is not None:
                filtered_df = filtered_df[filtered_df['Price'] <= max_price]
            
            if min_price is not None:
                filtered_df = filtered_df[filtered_df['Price'] >= min_price]
            
            # Apply rating filter if specified
            if min_rating is not None:
                filtered_df = filtered_df[filtered_df['Rating'] >= min_rating]
            
            # Apply stock filter if specified
            if min_stock is not None:
                filtered_df = filtered_df[filtered_df['Stock_Level'] >= min_stock]
            
            if filtered_df.empty:
                return f"No products found matching your criteria."
            
            # Sort by rating if "top" or "best" is in the query
            if "top" in query or "best" in query:
                filtered_df = filtered_df.sort_values('Rating', ascending=False)
            
            # Limit results to a reasonable number
            filtered_df = filtered_df.head(5)
            
            # Build response message
            response = "Here are the products matching your criteria:\n\n"
            response += "\n\n".join([self._format_product(p) for p in filtered_df.to_dict('records')])
            return response
            
        except Exception as e:
            print(f"Error in complex query: {str(e)}")
            return f"I'm having trouble processing your complex query. Please try a simpler question."
    
    def _format_product(self, product: Dict[str, Any]) -> str:
        """Format product details for display."""
        try:
            # Get column names dynamically
            name_col = next((col for col in ['Product_Name', 'ProductName', 'Name', 'product_name'] 
                            if col in product), 'N/A')
            category_col = next((col for col in ['Category', 'ProductCategory', 'product_category'] 
                               if col in product), 'N/A')
            price_col = next((col for col in ['Price', 'product_price', 'ProductPrice'] 
                            if col in product), 'N/A')
            rating_col = next((col for col in ['Rating', 'product_rating', 'ProductRating'] 
                             if col in product), 'N/A')
            stock_col = next((col for col in ['Stock_Level', 'StockLevel', 'stock', 'Inventory'] 
                            if col in product), 'N/A')
            
            name = product.get(name_col, 'N/A') if name_col != 'N/A' else 'N/A'
            category = product.get(category_col, 'N/A') if category_col != 'N/A' else 'N/A'
            price = product.get(price_col, 'N/A') if price_col != 'N/A' else 'N/A'
            rating = product.get(rating_col, 'N/A') if rating_col != 'N/A' else 'N/A'
            stock = product.get(stock_col, 'N/A') if stock_col != 'N/A' else 'N/A'
            
            return (
                f"Name: {name}\n"
                f"Category: {category}\n"
                f"Price: ${price}\n"
                f"Rating: {rating}/5.0\n"
                f"In Stock: {stock} units"
            )
        except Exception as e:
            print(f"Error formatting product: {str(e)}")
            # Fallback to a simpler format
            return "\n".join([f"{k}: {v}" for k, v in product.items() if k not in ['id', 'ID', 'product_id']]) 