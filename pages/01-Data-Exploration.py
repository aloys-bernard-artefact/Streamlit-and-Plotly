import streamlit as st
import plotly.express as px

st.snow()

def show_cat(sidebar: bool = True):
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/A-Cat.jpg/960px-A-Cat.jpg?20101227100718"
    if sidebar:
        st.sidebar.image(url, caption="Cat", use_container_width=True)
    else:
        st.image(url, caption="Cat", use_container_width=True)

st.sidebar.title("Celebrate 🎊")
if st.sidebar.button("Balloons! 🎈"):
    st.balloons()
show_cat(sidebar=True)

st.write("Streamlit is fun and open-source!") 
show_cat(sidebar=False)

df = px.data.iris()
fig = px.scatter_3d(df, x='sepal_length', y='sepal_width', z='petal_length',
                    color='species',
                    color_discrete_map={"setosa":"red", "versicolor":"green", "virginica":"blue"},
                    size='petal_width')

st.plotly_chart(fig)

