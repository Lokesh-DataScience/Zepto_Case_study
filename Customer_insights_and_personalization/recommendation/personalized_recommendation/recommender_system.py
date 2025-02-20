"""
-> This script contains the code for a personalized product recommendation system using a collaborative filtering approach. 
-> The system recommends products to a customer based on the products they have previously purchased. 
-> The recommendations are generated by calculating the cosine similarity between the products in the dataset and recommending products that are similar to the ones the customer has purchased.
"""

import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import os

class RecommenderSystem:
    def __init__(self, dataset_path):
        self.df = pd.read_csv(dataset_path)
        self.df.dropna(inplace=True)
        self.label_encoders = {}
        self._encode_features()
        self.product_features = self._create_product_features()
        self.product_similarity_df = self._calculate_similarity()

    def _encode_features(self):
        for column in ['Gender', 'City', 'Product_Category', 'Payment_Method', 'Age_Group', 'Loyalty_Tier']:
            le = LabelEncoder()
            self.df[column] = le.fit_transform(self.df[column])
            self.label_encoders[column] = le

    def _create_product_features(self):
        product_features = self.df[['Product_ID', 'Product_Category', 'Price', 'Competitor_Price', 'Ad_Click_Through_Rate', 'Browsing_Time_mins', 'Voice_Search_Count', 'Visual_Search_Count']].drop_duplicates().set_index('Product_ID')
        product_features[['Price', 'Competitor_Price', 'Ad_Click_Through_Rate', 'Browsing_Time_mins', 'Voice_Search_Count', 'Visual_Search_Count']] = product_features[['Price', 'Competitor_Price', 'Ad_Click_Through_Rate', 'Browsing_Time_mins', 'Voice_Search_Count', 'Visual_Search_Count']].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
        return product_features

    def _calculate_similarity(self):
        product_similarity = cosine_similarity(self.product_features)
        return pd.DataFrame(product_similarity, index=self.product_features.index, columns=self.product_features.index)

    def recommend_products(self, product_id, num_recommendations=5):
        similar_products = self.product_similarity_df[product_id].sort_values(ascending=False).head(num_recommendations + 1).index.tolist()
        similar_products.remove(product_id)
        return similar_products

    def recommend_products_for_customer(self, customer_id, num_recommendations=5):
        customer_data = self.df[self.df['Customer_ID'] == customer_id]
        if customer_data.empty:
            return [], [], "Unknown", "Unknown"
        
        customer_city_encoded = customer_data['City'].iloc[0]
        customer_city = self.label_encoders['City'].inverse_transform([customer_city_encoded])[0]
        customer_age_group_encoded = customer_data['Age_Group'].iloc[0]
        customer_age_group = self.label_encoders['Age_Group'].inverse_transform([customer_age_group_encoded])[0]
        
        recommended_products = set()
        for product_id in customer_data['Product_ID']:
            recommended_products.update(self.recommend_products(product_id, num_recommendations))
        recommended_products = list(recommended_products)[:num_recommendations]
        
        recommended_product_categories = self.df[self.df['Product_ID'].isin(recommended_products)][['Product_ID', 'Product_Category']].drop_duplicates(subset=['Product_ID'])
        recommended_product_categories['Product_Category'] = self.label_encoders['Product_Category'].inverse_transform(recommended_product_categories['Product_Category'])
        
        return recommended_products, recommended_product_categories['Product_Category'].tolist(), customer_city, customer_age_group

# Streamlit app
st.title("Customer Product Recommender")

dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Data', 'updated_dataset.csv'))
recommender = RecommenderSystem(dataset_path)

customer_id = st.text_input("Enter Customer ID:", "ZP_CUST4000")

if st.button("Get Recommendations"):
    customer_recommendations, product_categories, customer_city, customer_age_group = recommender.recommend_products_for_customer(customer_id)
    
    if not customer_recommendations:
        st.warning("No recommendations found for this customer ID. Please check the ID and try again.")
    else:
        st.subheader("Customer Details")
        st.write(f"**Customer ID:** {customer_id}")
        st.write(f"**Customer City:** {customer_city}")
        st.write(f"**Customer Age Group:** {customer_age_group}")
        
        st.subheader("Recommended Products")
        for prod, category in zip(customer_recommendations, product_categories):
            st.write(f"- **Product ID:** {prod} (Category: {category})")
