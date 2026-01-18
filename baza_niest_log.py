import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. POŁĄCZENIE
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn & Zamówienia", layout="wide")

# Funkcja do pobierania danych (używana przy odświeżaniu)
def get_data():
    prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("*").execute()
    return prod.data, kat.data

prod_data, kat_data = get_data()

st.title("📦 Inteligentny Magazyn")

# --- SEKCJA: ALERTY I SKŁADANIE ZAMÓWIENIA ---
st.header("🚨 Niskie stany i Zamówienia")

if prod_data:
    df = pd.DataFrame(prod_data)
    # Produkty do zamówienia (stan < 5)
    df_low_stock = df[df['liczba'] < 5].copy()

    if not df_low_stock.empty:
        st.warning(f"Masz {len(df_low_stock)} produkty wymagające uzupełnienia!")
        
        # Tabela zamówień
        cols = st.columns(len(df_low_stock) if len(df_low_stock) < 4 else 4)
        for idx, row in df_low_stock.iterrows():
            with cols[idx % 4]:
                st.error(f"**{row['nazwa']}**")
                st.write(f"Obecnie: {row['liczba']} szt.")
                
                # Prosty formularz zamówienia dla konkretnego produktu
                order_qty = st.number_input(f"Ilość do zamówienia", min_value=1, value=10, key=f"order_{row['id']}")
                if st.button(f"Zamów dla {row['nazwa']}", key=f"btn_{row['id']}"):
                    new_qty = row['liczba'] + order_qty
                    supabase.table("produkty").update({"liczba": new_qty}).eq("id", row['id']).execute()
                    st.success(f"Dostarczono {order_qty} szt.!")
                    st.rerun()
    else:
        st.success("Wszystkie stany magazynowe są w normie (powyżej 5 sztuk).")

st.divider()

# --- SEKCJA: ANALITYKA ---
if prod_data:
    st.subheader("📊 Analiza wizualna")
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.pie(df, names='kategoria_nazwa', title="Struktura asortymentu")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df, x='nazwa', y='liczba', color='liczba', 
                     title="Dokładny stan ilościowy", color_continuous_scale="RdYlGn")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- SEKCJA: ZARZĄDZANIE (PRODUKTY I KATEGORIE) ---
col_left, col_right = st.columns(2)

with col_left:
    st.header("🛒 Baza Produktów")
    if prod_data:
        # Wyświetlamy jako ładną tabelę z opcją usuwania pod spodem
        display_df = df[['id', 'nazwa', 'liczba', 'cena', 'kategoria_nazwa']]
        st.dataframe(display_df, use_container_width=True)
        
        with st.expander("Usuń produkt"):
            p_to_del = st.selectbox("Wybierz produkt do usunięcia", options=df['nazwa'].tolist())
            if st.button("Potwierdź usunięcie produktu"):
                p_id = df[df['nazwa'] == p_to_del]['id'].values[0]
                supabase.table("produkty").delete().eq("id", p_id).execute()
                st.rerun()

    with st.expander("➕ Dodaj nowy produkt"):
        with st.form("add_p"):
            n = st.text_input("Nazwa")
            l = st.number_input("Ilość początkowa", min_value=0)
            c = st.number_input("Cena (zł)", min_value=0.0)
            kat_opt = {k['nazwa']: k['id'] for k in kat_data}
            k_name = st.selectbox("Kategoria", options=list(kat_opt.keys()))
            if st.form_submit_button("Zapisz produkt"):
                supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria_id": kat_opt[k_name]}).execute()
                st.rerun()

with col_right:
    st.header("📂 Kategorie")
    if kat_data:
        for k in kat_data:
            c_a, c_b = st.columns([4, 1])
            c_a.write(f"**{k['nazwa']}**")
            if c_b.button("🗑️", key=f"del_k_{k['id']}"):
                supabase.table("kategorie").delete().eq("id", k['id']).execute()
                st.rerun()
    
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("add_k"):
            kn = st.text_input("Nazwa kategorii")
            if st.form_submit_button("Dodaj"):
                supabase.table("kategorie").insert({"nazwa": kn}).execute()
                st.rerun()
