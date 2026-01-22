import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. POŁĄCZENIE
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Pro", layout="wide")

def get_data():
    prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("*").execute()
    return prod.data, kat.data

prod_data, kat_data = get_data()

st.title("📦 System Magazynowy z Alertami")

# --- SEKCJA: ALERTY (DYNAMICZNE STANY MINIMALNE) ---
st.header("🚨 Uzupełnianie zapasów")

if prod_data:
    df = pd.DataFrame(prod_data)
    
    # Sprawdzamy, czy kolumna stan_minimalny istnieje, jeśli nie - przyjmujemy 5
    if 'stan_minimalny' not in df.columns:
        df['stan_minimalny'] = 5
    
    # Logika alertu: liczba < stan_minimalny
    df_to_order = df[df['liczba'] < df['stan_minimalny']].copy()

    if not df_to_order.empty:
        st.error(f"UWAGA: {len(df_to_order)} produktów poniżej zdefiniowanego stanu minimalnego!")
        
        cols = st.columns(len(df_to_order) if len(df_to_order) < 4 else 4)
        for idx, row in df_to_order.reset_index().iterrows():
            with cols[idx % 4]:
                st.info(f"**{row['nazwa']}**")
                st.write(f"Stan: {row['liczba']} / Min: {row['stan_minimalny']}")
                
                add_qty = st.number_input(f"Dodaj sztuk", min_value=1, value=10, key=f"order_{row['id']}")
                if st.button(f"Uzupełnij {row['nazwa']}", key=f"btn_{row['id']}"):
                    new_qty = row['liczba'] + add_qty
                    supabase.table("produkty").update({"liczba": new_qty}).eq("id", row['id']).execute()
                    st.success("Zaktualizowano!")
                    st.rerun()
    else:
        st.success("Wszystkie produkty mają stan powyżej minimum.")

st.divider()

# --- SEKCJA: ANALITYKA ---
if prod_data:
    st.subheader("📊 Wizualizacja stanów")
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    
    c1, c2 = st.columns(2)
    with c1:
        # Wykres pokazujący ile brakuje do stanu minimalnego
        df['procent_normy'] = (df['liczba'] / df['stan_minimalny'] * 100).clip(upper=200)
        fig2 = px.bar(df, x='nazwa', y='liczba', color='procent_normy',
                     title="Stan produktów względem ich limitów",
                     color_continuous_scale="RdYlGn",
                     labels={'procent_normy': '% Normy'})
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        fig1 = px.pie(df, names='kategoria_nazwa', title="Podział asortymentu")
        st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- SEKCJA: ZARZĄDZANIE ---
col_l, col_r = st.columns(2)

with col_l:
    st.header("🛒 Produkty")
    if prod_data:
        # Wyświetlamy tabelę z widocznym stanem minimalnym
        st.dataframe(df[['id', 'nazwa', 'liczba', 'stan_minimalny', 'cena', 'kategoria_nazwa']], use_container_width=True)
        
        with st.expander("Usuń produkt"):
            p_to_del = st.selectbox("Wybierz produkt", options=df['nazwa'].tolist())
            if st.button("Usuń trwale"):
                p_id = df[df['nazwa'] == p_to_del]['id'].values[0]
                supabase.table("produkty").delete().eq("id", p_id).execute()
                st.rerun()

    with st.expander("➕ Dodaj produkt ze stanem minimalnym"):
        with st.form("add_p_new"):
            name = st.text_input("Nazwa")
            qty = st.number_input("Aktualna ilość", min_value=0)
            min_qty = st.number_input("Stan minimalny (alert)", min_value=0, value=5)
            price = st.number_input("Cena", min_value=0.0)
            
            kat_opt = {k['nazwa']: k['id'] for k in kat_data}
            k_choice = st.selectbox("Kategoria", options=list(kat_opt.keys()))
            
            if st.form_submit_button("Dodaj do bazy"):
                supabase.table("produkty").insert({
                    "nazwa": name, 
                    "liczba": qty, 
                    "stan_minimalny": min_qty, 
                    "cena": price, 
                    "kategoria_id": kat_opt[k_choice]
                }).execute()
                st.rerun()

with col_r:
    st.header("📂 Kategorie")
    for k in kat_data:
        cl1, cl2 = st.columns([4, 1])
        cl1.write(f"**{k['nazwa']}**")
        if cl2.button("🗑️", key=f"dk_{k['id']}"):
            supabase.table("kategorie").delete().eq("id", k['id']).execute()
            st.rerun()
            
    with st.expander("➕ Nowa kategoria"):
        with st.form("add_k"):
            kn = st.text_input("Nazwa")
            if st.form_submit_button("Dodaj"):
                supabase.table("kategorie").insert({"nazwa": kn}).execute()
                st.rerun()
                
