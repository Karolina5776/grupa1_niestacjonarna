import streamlit as st
from supabase import create_client, Client

# 1. Połączenie z bazą (Dane pobierane z Secrets TOML)
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.title("Zarządzanie Produktami (Supabase)")

# --- SEKCJA KATEGORII ---
st.header("📂 Kategorie")
with st.form("new_category"):
    nazwa_kat = st.text_input("Nazwa nowej kategorii")
    opis_kat = st.text_input("Opis")
    if st.form_submit_button("Dodaj kategorię"):
        supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
        st.success("Dodano!")
        st.rerun()

# Wyświetlanie i usuwanie kategorii
kat_data = supabase.table("kategorie").select("*").execute()
if kat_data.data:
    df_kat = sorted(kat_data.data, key=lambda x: x['id'])
    for k in df_kat:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{k['nazwa']}** (ID: {k['id']})")
        if col2.button("Usuń", key=f"del_kat_{k['id']}"):
            supabase.table("kategorie").delete().eq("id", k['id']).execute()
            st.rerun()

st.divider()

# --- SEKCJA PRODUKTÓW ---
st.header("🛒 Produkty")
with st.form("new_product"):
    p_nazwa = st.text_input("Nazwa produktu")
    p_liczba = st.number_input("Ilość", min_value=0)
    p_cena = st.number_input("Cena", min_value=0.0)
    
    # Lista kategorii do wyboru
    options = {k['nazwa']: k['id'] for k in kat_data.data}
    p_kat = st.selectbox("Wybierz kategorię", options=list(options.keys()))
    
    if st.form_submit_button("Dodaj produkt"):
        supabase.table("produkty").insert({
            "nazwa": p_nazwa, 
            "liczba": p_liczba, 
            "cena": p_cena, 
            "kategoria_id": options[p_kat]
        }).execute()
        st.success("Produkt dodany!")
        st.rerun()

# Wyświetlanie produktów
prod_data = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
if prod_data.data:
    for p in prod_data.data:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{p['nazwa']}** - {p['liczba']} szt.")
        col2.write(f"Kat: {p['kategorie']['nazwa'] if p['kategorie'] else 'Brak'}")
        if col3.button("Usuń", key=f"del_prod_{p['id']}"):
            supabase.table("produkty").delete().eq("id", p['id']).execute()
            st.rerun()


import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# ... (tutaj Twoja inicjalizacja połączenia supabase) ...

# --- SEKCJA ANALITYKI (STATYSTYKI) ---
st.header("📊 Analiza Magazynu")

# Pobieranie danych do DataFrame
prod_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
if prod_res.data:
    df = pd.DataFrame(prod_res.data)
    # Rozwinięcie nazwy kategorii z relacji
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')

    # 1. Wskaźniki na górze
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Liczba produktów", len(df))
    col_m2.metric("Łączna ilość sztuk", int(df['liczba'].sum()))
    total_value = (df['liczba'] * df['cena']).sum()
    col_m3.metric("Wartość magazynu", f"{total_value:,.2f} zł")

    # 2. Wykresy w dwóch kolumnach
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Struktura kategorii")
        fig_pie = px.pie(df, names='kategoria_nazwa', title="Udział kategorii w magazynie")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Stany ilościowe")
        fig_bar = px.bar(df, x='nazwa', y='liczba', color='kategoria_nazwa', 
                         title="Ilość sztuk per produkt", labels={'nazwa': 'Produkt', 'liczba': 'Ilość'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # 3. Alerty niskiego stanu
    low_stock = df[df['liczba'] < 5] # Produkty, których jest mniej niż 5
    if not low_stock.empty:
        st.warning(f"⚠️ Uwaga! Niskie stany magazynowe dla: {', '.join(low_stock['nazwa'].tolist())}")
else:
    st.info("Dodaj pierwsze produkty, aby zobaczyć statystyki.")
