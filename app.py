import streamlit as st
import pandas as pd
from statsbombpy import sb
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import seaborn as sns

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Messi Dashboard", layout="wide", page_icon="⚽")

st.title("🐐 Lionel Messi Analysis Dashboard")
st.markdown("Визуализация данных StatsBomb Open Data с использованием Streamlit и Mplsoccer.")

# --- КЭШИРОВАНИЕ ДАННЫХ ---
@st.cache_data
def load_competitions():
    comps = sb.competitions()
    return comps[comps['country_name'] == 'Spain']

@st.cache_data
def load_matches(competition_id, season_id):
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    return matches.sort_values('match_date')

@st.cache_data
def load_match_events(match_id):
    events = sb.events(match_id=match_id)
    return events

# --- SIDEBAR ---
st.sidebar.header("Фильтры")
comps = load_competitions()
la_liga = comps[comps['competition_id'] == 11]
season_options = la_liga['season_name'].unique()

selected_season = st.sidebar.selectbox("Выберите сезон", season_options)

selected_match_str = None
if selected_season:
    season_info = la_liga[la_liga['season_name'] == selected_season].iloc[0]
    comp_id = season_info['competition_id']
    seas_id = season_info['season_id']
    matches = load_matches(comp_id, seas_id)
    match_display = matches.apply(lambda x: f"{x['home_team']} vs {x['away_team']} ({x['match_date']})", axis=1)
    selected_match_str = st.sidebar.selectbox("Выберите матч", match_display)
    selected_match_id = matches.iloc[match_display[match_display == selected_match_str].index[0]]['match_id']

# --- ОСНОВНАЯ ЧАСТЬ ---
if selected_match_str:
    st.subheader(f"Анализ матча: {selected_match_str}")
    events = load_match_events(selected_match_id)
    messi_id = 5503
    messi_events = events[events['player_id'] == messi_id]
    
    if messi_events.empty:
        st.warning("В этом матче Месси не совершал активных действий (или его нет в данных).")
    else:
        tab1, tab2, tab3 = st.tabs(["📊 Статистика", "🎯 Карта ударов", "🗺️ Тепловая карта"])
        
        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            goals = len(messi_events[(messi_events['type'] == 'Shot') & (messi_events['shot_outcome'] == 'Goal')])
            assists = len(messi_events[messi_events['pass_goal_assist'] == True])
            shots = len(messi_events[messi_events['type'] == 'Shot'])
            xg = messi_events[messi_events['type'] == 'Shot']['shot_statsbomb_xg'].sum()
            col1.metric("Голы", goals)
            col2.metric("Ассисты", assists)
            col3.metric("Удары", shots)
            col4.metric("xG", f"{xg:.2f}")
            st.dataframe(messi_events[['minute', 'type', 'location', 'shot_outcome']].dropna(axis=1, how='all'))

        with tab2:
            shots_df = messi_events[messi_events['type'] == 'Shot'].copy()
            if not shots_df.empty:
                pitch = Pitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#aabb97', line_color='white')
                fig, ax = pitch.draw(figsize=(10, 7))
                shots_df['x'] = shots_df['location'].apply(lambda x: x[0])
                shots_df['y'] = shots_df['location'].apply(lambda x: x[1])
                sc = pitch.scatter(shots_df.x, shots_df.y, ax=ax, s=shots_df['shot_statsbomb_xg']*500+100, c='red', edgecolors='black')
                st.pyplot(fig)
            else:
                st.write("Нет ударов.")

        with tab3:
            action_events = messi_events[messi_events['location'].notna()].copy()
            if not action_events.empty:
                action_events['x'] = action_events['location'].apply(lambda x: x[0])
                action_events['y'] = action_events['location'].apply(lambda x: x[1])
                pitch = Pitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#22312b', line_color='#c7d5cc')
                fig, ax = pitch.draw(figsize=(10, 7))
                sns.kdeplot(x=action_events['x'], y=action_events['y'], fill=True, cmap='inferno', alpha=0.6, ax=ax)
                st.pyplot(fig)
