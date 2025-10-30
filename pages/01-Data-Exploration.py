import streamlit as st
import plotly.express as px

st.write("Streamlit is fun and open-source!") 

df = px.data.iris()
fig = px.scatter_3d(df, x='sepal_length', y='sepal_width', z='petal_length',
                    color='species',
                    color_discrete_map={"setosa":"red", "versicolor":"green", "virginica":"blue"},
                    size='petal_width')

st.plotly_chart(fig)

