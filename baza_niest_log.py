import streamlit as st
from supabase import create_client, Client

# Funkcja inicjalizująca połączenie z Supabase za pomocą URL i KEY
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_connection()

# PRZYKŁAD: Pobieranie produktów (zamiast starego run_query)
def get_products():
    # .table("produkty") odpowiada Twojej tabeli z obrazka
    response = supabase.table("produkty").select("*").execute()
    return response.data

st.title("Twoja Aplikacja")
# Wyświetlenie danych
dane = get_products()
st.write(dane)

# --- SEKCJA KATEGORII ---
st.header("📂 kategorie")

tab1, tab2 = st.tabs(["Lista i Usuwanie", "Dodaj Nową"])

with tab1:
    categories = run_query("SELECT * FROM kategorie ORDER BY id ASC")
    if categories:
        df_cat = pd.DataFrame(categories, columns=["ID", "Nazwa", "Opis"])
        st.table(df_cat)
        
        cat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", df_cat["Nazwa"])
        if st.button("Usuń kategorię"):
            run_query("DELETE FROM kategorie WHERE nazwa = %s", (cat_to_delete,), commit=True)
            st.success(f"Usunięto kategorię: {cat_to_delete}")
            st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

with tab2:
    with st.form("add_category"):
        new_cat_name = st.text_input("Nazwa kategorii")
        new_cat_desc = st.text_area("Opis")
        if st.form_submit_button("Zapisz kategorię"):
            run_query("INSERT INTO kategorie (nazwa, opis) VALUES (%s, %s)", (new_cat_name, new_cat_desc), commit=True)
            st.success("Dodano nową kategorię!")
            st.rerun()

st.divider()

# --- SEKCJA PRODUKTÓW ---
st.header("🛒 Produkty")

p_tab1, p_tab2 = st.tabs(["Lista i Usuwanie", "Dodaj Nowy"])

with p_tab1:
    products = run_query("""
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa 
        FROM produkty p 
        LEFT JOIN kategorie k ON p.kategoria_id = k.id 
        ORDER BY p.id DESC
    """)
    if products:
        df_prod = pd.DataFrame(products, columns=["ID", "Produkt", "Ilość", "Cena", "Kategoria"])
        st.dataframe(df_prod, use_container_width=True)
        
        prod_id_to_delete = st.number_input("Podaj ID produktu do usunięcia", step=1, min_value=1)
        if st.button("Usuń produkt"):
            run_query("DELETE FROM produkty WHERE id = %s", (prod_id_to_delete,), commit=True)
            st.warning(f"Usunięto produkt o ID: {prod_id_to_delete}")
            st.rerun()
    else:
        st.info("Brak produktów.")

with p_tab2:
    with st.form("add_product"):
        p_name = st.text_input("Nazwa produktu")
        p_qty = st.number_input("Ilość", min_value=0, step=1)
        p_price = st.number_input("Cena", min_value=0.0, format="%.2f")
        
        # Pobranie kategorii do selectboxa
        cat_options = run_query("SELECT id, nazwa FROM kategorie")
        cat_dict = {name: id for id, name in cat_options}
        p_cat_name = st.selectbox("Kategoria", options=list(cat_dict.keys()))
        
        if st.form_submit_button("Dodaj produkt"):
            run_query(
                "INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (%s, %s, %s, %s)",
                (p_name, p_qty, p_price, cat_dict[p_cat_name]),
                commit=True
            )
            st.success("Produkt dodany!")
            st.rerun()
