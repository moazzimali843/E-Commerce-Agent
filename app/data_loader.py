import pandas as pd
from typing import Dict, List, Any

def load_product_data(file_path: str = "Product_statistics.csv") -> pd.DataFrame:
    """Load product data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading product data: {e}")
        return pd.DataFrame()

def load_faq_data(file_path: str = "FAQ.csv") -> pd.DataFrame:
    """Load FAQ data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading FAQ data: {e}")
        return pd.DataFrame()

def filter_products(
    df: pd.DataFrame,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rating: float = None,
    min_stock: int = None
) -> pd.DataFrame:
    """Filter products based on criteria."""
    filtered_df = df.copy()
    
    if category:
        filtered_df = filtered_df[filtered_df['Category'].str.contains(category, case=False)]
    
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['Price'] >= min_price]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['Price'] <= max_price]
    
    if min_rating is not None:
        filtered_df = filtered_df[filtered_df['Rating'] >= min_rating]
    
    if min_stock is not None:
        filtered_df = filtered_df[filtered_df['Stock_Level'] >= min_stock]
    
    return filtered_df

def get_product_details(df: pd.DataFrame, product_id: int = None, product_name: str = None) -> Dict[str, Any]:
    """Get details for a specific product by ID or name."""
    if product_id is not None:
        product = df[df['Product_ID'] == product_id]
    elif product_name is not None:
        product = df[df['Product_Name'].str.contains(product_name, case=False)]
    else:
        return {}
    
    if product.empty:
        return {}
    
    return product.iloc[0].to_dict()

def get_top_products(df: pd.DataFrame, category: str = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Get top-rated products, optionally filtered by category."""
    filtered_df = df.copy()
    
    if category:
        filtered_df = filtered_df[filtered_df['Category'].str.contains(category, case=False)]
    
    # Sort by rating in descending order
    top_products = filtered_df.sort_values('Rating', ascending=False).head(limit)
    
    return top_products.to_dict('records') 