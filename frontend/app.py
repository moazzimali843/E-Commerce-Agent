import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoint from .env file
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Function to load product data directly
def load_product_data():
    try:
        return pd.read_csv("Product_statistics.csv")
    except Exception as e:
        st.error(f"Error loading product data: {e}")
        return pd.DataFrame()

# Set page config
st.set_page_config(
    page_title="Product Assistant",
    page_icon="🛍️",
    layout="wide"
)

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Chat Assistant", "Product Filters", "Product Analytics"])

with tab1:
    st.title("🛍️ AI Product Assistant")
    st.markdown("""
    This assistant can help you with:
    - Answering questions about shipping, returns, and other policies
    - Providing product recommendations
    """)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask about our products or policies..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Send request to API
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": prompt}
                )
                
                if response.status_code == 200:
                    assistant_response = response.json()["response"]
                    message_placeholder.markdown(assistant_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    message_placeholder.markdown(f"Error: {response.text}")
            except Exception as e:
                message_placeholder.markdown(f"Error connecting to API: {str(e)}")

with tab2:
    st.title("🔍 Product Filters")
    st.markdown("Use the filters below to find products that match your criteria.")
    
    # Load product data
    products_df = load_product_data()
    
    if not products_df.empty:
        # Create filter sidebar
        col1, col2 = st.columns(2)
        
        with col1:
            # Category filter
            categories = ["All"] + sorted(products_df["Category"].unique().tolist())
            selected_category = st.selectbox("Select Category", categories)
            
            # Price range filter
            min_price = int(products_df["Price"].min())
            max_price = int(products_df["Price"].max())
            price_range = st.slider("Price Range ($)", min_price, max_price, (min_price, max_price))
        
        with col2:
            # Rating filter
            min_rating = float(products_df["Rating"].min())
            max_rating = float(products_df["Rating"].max())
            rating_filter = st.slider("Minimum Rating", min_rating, max_rating, min_rating, 0.1)
            
            # Stock filter
            in_stock_only = st.checkbox("Show only in-stock items")
        
        # Apply filters
        filtered_df = products_df.copy()
        
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["Category"] == selected_category]
        
        filtered_df = filtered_df[
            (filtered_df["Price"] >= price_range[0]) & 
            (filtered_df["Price"] <= price_range[1]) &
            (filtered_df["Rating"] >= rating_filter)
        ]
        
        if in_stock_only:
            filtered_df = filtered_df[filtered_df["Stock_Level"] > 0]
        
        # Display results
        st.subheader(f"Found {len(filtered_df)} products matching your criteria")
        
        # Sort options
        sort_options = {
            "Price (Low to High)": ("Price", True),
            "Price (High to Low)": ("Price", False),
            "Rating (High to Low)": ("Rating", False),
            "Stock Level (High to Low)": ("Stock_Level", False)
        }
        
        sort_by = st.selectbox("Sort by", list(sort_options.keys()))
        sort_col, ascending = sort_options[sort_by]
        filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)
        
        # Display products in a nice format
        for _, product in filtered_df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    # Display a placeholder icon based on category
                    if product["Category"] == "Electronics":
                        st.markdown("🔌")
                    elif product["Category"] == "Computers":
                        st.markdown("💻")
                    elif product["Category"] == "Wearables":
                        st.markdown("⌚")
                    elif product["Category"] == "Accessories":
                        st.markdown("🎧")
                    else:
                        st.markdown("📦")
                
                with col2:
                    st.markdown(f"### {product['Product_Name']}")
                    st.markdown(f"**Category:** {product['Category']}")
                    st.markdown(f"**Price:** ${product['Price']}")
                    st.markdown(f"**Rating:** {'⭐' * int(product['Rating'])} ({product['Rating']})")
                    
                    # Show stock status with color
                    if product["Stock_Level"] > 50:
                        st.markdown(f"**Stock:** :green[{product['Stock_Level']} units available]")
                    elif product["Stock_Level"] > 0:
                        st.markdown(f"**Stock:** :orange[{product['Stock_Level']} units available]")
                    else:
                        st.markdown(f"**Stock:** :red[Out of stock]")
                
                st.markdown("---")
    else:
        st.error("Unable to load product data. Please check your data file.")

with tab3:
    st.title("📊 Product Analytics")
    st.markdown("Explore product statistics and trends.")
    
    # Load product data
    products_df = load_product_data()
    
    if not products_df.empty:
        # Create multiple visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Products by Category")
            fig1 = px.pie(
                products_df, 
                names="Category", 
                values="Sales_Count",
                title="Sales Distribution by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            st.subheader("Price vs. Rating")
            fig3 = px.scatter(
                products_df,
                x="Price",
                y="Rating",
                size="Sales_Count",
                color="Category",
                hover_name="Product_Name",
                title="Price vs. Rating (size represents sales volume)",
                labels={"Price": "Price ($)", "Rating": "Rating (out of 5)"}
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            st.subheader("Top Products by Sales")
            top_products = products_df.sort_values("Sales_Count", ascending=False).head(5)
            fig2 = px.bar(
                top_products,
                x="Product_Name",
                y="Sales_Count",
                color="Category",
                title="Top 5 Products by Sales",
                labels={"Product_Name": "Product", "Sales_Count": "Units Sold"}
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("Stock Levels by Product")
            fig4 = px.bar(
                products_df,
                x="Product_Name",
                y="Stock_Level",
                color="Category",
                title="Current Stock Levels",
                labels={"Product_Name": "Product", "Stock_Level": "Units in Stock"}
            )
            # Add a horizontal line for average stock level
            avg_stock = products_df["Stock_Level"].mean()
            fig4.add_shape(
                type="line",
                x0=-0.5,
                x1=len(products_df)-0.5,
                y0=avg_stock,
                y1=avg_stock,
                line=dict(color="red", width=2, dash="dash")
            )
            fig4.add_annotation(
                x=len(products_df)/2,
                y=avg_stock*1.1,
                text=f"Avg Stock: {avg_stock:.0f}",
                showarrow=False,
                font=dict(color="red")
            )
            st.plotly_chart(fig4, use_container_width=True)
        
        # Additional analytics section
        st.subheader("Key Performance Metrics")
        
        # Create metrics row
        metric1, metric2, metric3, metric4 = st.columns(4)
        
        with metric1:
            total_sales = products_df["Sales_Count"].sum()
            st.metric("Total Sales", f"{total_sales:,}")
        
        with metric2:
            avg_rating = products_df["Rating"].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}/5.0")
        
        with metric3:
            avg_price = products_df["Price"].mean()
            st.metric("Average Price", f"${avg_price:.2f}")
        
        with metric4:
            total_stock = products_df["Stock_Level"].sum()
            st.metric("Total Inventory", f"{total_stock:,} units")
        
        # Category performance comparison
        st.subheader("Category Performance")
        category_stats = products_df.groupby("Category").agg({
            "Sales_Count": "sum",
            "Rating": "mean",
            "Price": "mean",
            "Stock_Level": "sum"
        }).reset_index()
        
        # Create a radar chart for category comparison
        categories = category_stats["Category"].tolist()
        fig5 = go.Figure()
        
        # Normalize the metrics for radar chart
        metrics = ["Sales_Count", "Rating", "Price", "Stock_Level"]
        normalized_data = category_stats.copy()
        
        for metric in metrics:
            max_val = normalized_data[metric].max()
            normalized_data[f"{metric}_norm"] = normalized_data[metric] / max_val
        
        # Add traces for each category
        for i, category in enumerate(categories):
            cat_data = normalized_data[normalized_data["Category"] == category]
            fig5.add_trace(go.Scatterpolar(
                r=[
                    cat_data["Sales_Count_norm"].values[0],
                    cat_data["Rating_norm"].values[0],
                    cat_data["Price_norm"].values[0],
                    cat_data["Stock_Level_norm"].values[0],
                    cat_data["Sales_Count_norm"].values[0]  # Close the loop
                ],
                theta=["Sales", "Rating", "Price", "Stock", "Sales"],
                fill="toself",
                name=category
            ))
        
        fig5.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title="Category Performance Comparison (Normalized)"
        )
        
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.error("Unable to load product data. Please check your data file.")

# Sidebar with example questions (only shown in Chat tab)
with st.sidebar:
    st.header("Example Questions")
    
    st.subheader("Product Queries")
    example_product_queries = [
        "What electronics do you have under $200?",
        "Tell me about the Laptop Pro",
        "What are your top-rated accessories?",
        "Do you have any smartwatches in stock?",
    ]
    
    for query in example_product_queries:
        if st.button(query, key=f"product_{query}"):
            # Clear input and add to chat
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.subheader("FAQ Queries")
    example_faq_queries = [
        "What is your return policy?",
        "Do you ship internationally?",
        "How can I track my order?",
        "What payment methods do you accept?",
    ]
    
    for query in example_faq_queries:
        if st.button(query, key=f"faq_{query}"):
            # Clear input and add to chat
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun() 