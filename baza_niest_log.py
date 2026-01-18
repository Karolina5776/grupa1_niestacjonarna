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
