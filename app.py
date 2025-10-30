import streamlit as st 

# Ecrire du texte
st.title("Streamlit Demo")


# Récupérer l'input de l'utilisateur  
nom = st.text_input("Nom","Jane Doe")
num = st.number_input("Choisis un nombre entre 0 et 7"
                      , min_value=0
                      , max_value=7)

birth_year = st.slider( "Pick a Birthyear"
                         ,min_value=1950
                         ,max_value=2025)

if st.button("Click me"): 
    st.balloons()
    st.write(f"Tu as {2025 -  birth_year} ans ! ")
    st.write(f"Hello {nom}")

st.markdown("""
            [Lien](url)
            ![](https://cdn.pixabay.com/photo/2015/11/16/14/43/cat-1045782_640.jpg)
            ## Subheader
            ### SubsubHEader
            * Bulletlist
            * Bulletlist
            
            """)