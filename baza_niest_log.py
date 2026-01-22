import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide")

# --- STYLE CSS (Tło, JASNY NIEBIESKI) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    
    html, body, [class*="st-"], h1, h2, h3, h4, h5, h6, p, label {
        color: #1E90FF !important;
        font-weight: bold;
    }
    
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; border-radius: 10px; border: 2px solid #1E90FF;
    }
    
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #1E90FF !important; }

    .stExpander { 
        background-color: rgba(255, 255, 255, 0.9) !important; 
        border: 1px solid #1E90FF !important; 
    }
    
    button[data-baseweb="tab"] p { color: #1E90FF !important; }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

# --- SEKCJA WIZUALIZACJI (WYKRESY I STATYSTYKI) ---
if prod_data:
    df = pd.DataFrame(prod_data)
    # Przygotowanie danych
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    df['liczba'] = pd.to_numeric(df['liczba'], errors='coerce').fillna(0)
    df['cena'] = pd.to_numeric(df['cena'], errors='coerce').fillna(0)
    
    # Statystyki KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    c2.metric("💰 Wartość", f"{round((df['liczba'] * df['cena']).sum(), 2)} zł")
    c3.metric("⚠️ Alerty", len(df[df['liczba'] < 5]))
    c4.metric("📂 Kategorie", len(kat_data))

    # WYKRESY - Teraz na pewno się wyświetlą, gdy są dane
    col_l, col_r = st.columns([1, 1.5])
    with col_l:
        fig_pie = px.pie(df, values='liczba', names='kategoria_nazwa', hole=0.4, 
                         title="Udział kategorii", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_r:
        fig_bar = px.bar(df, x='nazwa', y='liczba', color='kategoria_nazwa', 
                         title="Stan magazynowy poszczególnych produktów")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Lista Produktów")
    st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'cena']], use_container_width=True)
else:
    st.info("Magazyn jest obecnie pusty. Dodaj pierwszy produkt w zakładce poniżej! 👇")

st.divider()

# --- SEKCJA OPERACJI ---
t1, t2, t3 = st.tabs(["🆕 Produkty", "🚚 Dostawa", "📂 Kategorie"])

with t1:
    st.subheader("Dodaj Produkt")
    with st.form("p_form"):
        n = st.text_input("Nazwa produktu")
        q = st.number_input("Ilość", min_value=0, value=0)
        p = st.number_input("Cena", min_value=0.0, value=0.0)
        
        kat_options = [k['nazwa'] for k in kat_data]
        kat_options.append("+ Dodaj nową kategorię...")
        k_sel = st.selectbox("Wybierz kategorię", options=kat_options)
        
        new_kat_input = st.text_input("Nazwa nowej kategorii (jeśli wybrano opcję powyżej)")
        
        if st.form_submit_button("Zapisz Produkt"):
            try:
                final_kat_id = None
                if k_sel == "+ Dodaj nową kategorię...":
                    if new_kat_input:
                        new_k_res = supabase.table("kategorie").insert({"nazwa": new_kat_input}).execute()
                        final_kat_id = new_k_res.data[0]['id']
                    else:
                        st.error("Wpisz nazwę nowej kategorii!")
                        st.stop()
                else:
                    final_kat_id = next(k['id'] for k in kat_data if k['nazwa'] == k_sel)
                
                supabase.table("produkty").insert({
                    "nazwa": n, "liczba": q, "cena": p, "kategoria_id": final_kat_id
                }).execute()
                st.success("Dodano produkt!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {e}")

with t2:
    if prod_data:
        p_name = st.selectbox("Wybierz produkt", options=[p['nazwa'] for p in prod_data])
        amount = st.number_input("Dodaj ilość", min_value=1)
        if st.button("Zaktualizuj"):
            row = next(item for item in prod_data if item["nazwa"] == p_name)
            supabase.table("produkty").update({"liczba": int(row['liczba']) + amount}).eq("id", row['id']).execute()
            st.rerun()

with t3:
    with st.form("k_form_standalone"):
        nk = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj"):
            if nk:
                supabase.table("kategorie").insert({"nazwa": nk}).execute()
                st.rerun()
