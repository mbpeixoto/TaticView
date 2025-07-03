import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import plotly.express as px
import time
from config import METRICS_CSV_PATH, POSITIONS_CSV_PATH,  CAMERA_VIEW, TEAM_COLORS_DASH, BALL_COLOR_DASH
import plotly.graph_objects as go
import matplotlib.colors as mcolors

# Carrega os dados
@st.cache_data
def load_data():
    df_metrics = pd.read_csv(METRICS_CSV_PATH)
    df_positions = pd.read_csv(POSITIONS_CSV_PATH)
    df_positions["positions"] = df_positions["positions"].apply(json.loads)
    return df_metrics, df_positions

df_metrics, df_positions = load_data()
df_metrics["tempo"] = df_metrics["frame"] / 30.0


# Interface
st.title("Análise Defensiva - Dashboard Tático")

# Sidebar de configuração dinâmica
st.sidebar.subheader("⚙️ Configurações do Campo 2D")

show_lines = st.sidebar.checkbox("Mostrar marcações do campo", value=True)
field_scale_x = st.sidebar.slider("Escala da Largura (X - lateral)", 0.5, 2.0, 1.0, step=0.1)
field_scale_y = st.sidebar.slider("Escala da Altura (Y - gol a gol)", 0.5, 2.0, 1.0, step=0.1)



# Campo 2D com movimentação dos jogadores
st.subheader("Campo 2D com movimentação dos jogadores")

df_positions["timestamp"] = df_positions["frame"] / 30.0  # considera 30 FPS

# Ajusta para que Y seja profundidade (gol a gol) e X seja lateral (campo 800x500)
def get_position(row, view = CAMERA_VIEW):
    pontos = np.array(row["positions"])
    if view == "behind_goal":
        return [(x, y) for x, y in pontos]  # X=lateral, Y=profundidade
    else:
        return [(y, x) for x, y in pontos]  # troca se for visão lateral

df_positions["pts"] = df_positions.apply(lambda row: get_position(row), axis=1)

# Animação automática com botão Play
min_time = df_positions["timestamp"].min()
max_time = df_positions["timestamp"].max()

if "play" not in st.session_state:
    st.session_state.play = False

col1, col2 = st.columns([1, 4])
if col1.button("▶ Play" if not st.session_state.play else "⏸ Pause"):
    st.session_state.play = not st.session_state.play

frame_placeholder = col2.empty()

field_width, field_height = 800, 500

# Função para desenhar o campo
def draw_field(ax, view="behind_goal", show_lines=True):
    # Tamanho base (campo padrão 105x68m ≈ 800x520 px)
    base_width, base_height = (520, 800) if view == "behind_goal" else (800, 520)
    field_width = base_width * field_scale_x
    field_height = base_height * field_scale_y

    ax.set_facecolor("green")
    ax.set_xlim(0, field_width)
    ax.set_ylim(field_height, 0)
    ax.set_title("Campo 2D - Animação")
    ax.set_xlabel("Largura (X)")
    ax.set_ylabel("Profundidade (Y)")

    if not show_lines:
        return

    # Marcação do campo (linhas brancas)
    ax.plot([0, field_width], [0, 0], color='white')
    ax.plot([0, field_width], [field_height, field_height], color='white')
    ax.plot([0, 0], [0, field_height], color='white')
    ax.plot([field_width, field_width], [0, field_height], color='white')
    ax.axhline(field_height / 2, color='white', linestyle='--')

    goal_area_width = 200 * field_scale_x
    goal_area_depth = 60 * field_scale_y

    if view == "behind_goal":
        # Área inferior
        ax.plot([field_width/2 - goal_area_width/2, field_width/2 - goal_area_width/2],
                [field_height, field_height - goal_area_depth], color='white')
        ax.plot([field_width/2 + goal_area_width/2, field_width/2 + goal_area_width/2],
                [field_height, field_height - goal_area_depth], color='white')
        ax.plot([field_width/2 - goal_area_width/2, field_width/2 + goal_area_width/2],
                [field_height - goal_area_depth, field_height - goal_area_depth], color='white')

        # Área superior
        ax.plot([field_width/2 - goal_area_width/2, field_width/2 - goal_area_width/2],
                [0, goal_area_depth], color='white')
        ax.plot([field_width/2 + goal_area_width/2, field_width/2 + goal_area_width/2],
                [0, goal_area_depth], color='white')
        ax.plot([field_width/2 - goal_area_width/2, field_width/2 + goal_area_width/2],
                [goal_area_depth, goal_area_depth], color='white')
    else:
        # Área lateral (visão de lado)
        ax.plot([0, goal_area_depth],
                [field_height/2 - goal_area_width/2, field_height/2 - goal_area_width/2], color='white')
        ax.plot([0, goal_area_depth],
                [field_height/2 + goal_area_width/2, field_height/2 + goal_area_width/2], color='white')
        ax.plot([goal_area_depth, goal_area_depth],
                [field_height/2 - goal_area_width/2, field_height/2 + goal_area_width/2], color='white')

        ax.plot([field_width - goal_area_depth, field_width],
                [field_height/2 - goal_area_width/2, field_height/2 - goal_area_width/2], color='white')
        ax.plot([field_width - goal_area_depth, field_width],
                [field_height/2 + goal_area_width/2, field_height/2 + goal_area_width/2], color='white')
        ax.plot([field_width - goal_area_depth, field_width - goal_area_depth],
                [field_height/2 - goal_area_width/2, field_height/2 + goal_area_width/2], color='white')


# Cores de cada time
team_colors = TEAM_COLORS_DASH

if st.session_state.play:
    current_time = min_time
    start_time = time.perf_counter()
    frame_interval = 1 / 30.0  # 30 FPS

    while current_time <= max_time and st.session_state.play:
        # Verifica tempo real decorrido desde o início do play
        elapsed_time = time.perf_counter() - start_time
        current_time = min_time + elapsed_time

        # Seleciona o frame mais próximo do tempo atual
        frame_data = df_positions[np.isclose(df_positions["timestamp"], current_time, atol=1/30)]

        # Renderiza o campo e os jogadores
        fig, ax = plt.subplots(figsize=(10 * field_scale_x, 6 * field_scale_y))

        draw_field(ax, view=CAMERA_VIEW, show_lines=show_lines)

        for team_id, group in frame_data.groupby("team"):
            all_xs, all_ys = [], []
            for _, row in group.iterrows():
                xys = row["pts"]
                xs, ys = zip(*xys)
                all_xs.extend(xs)
                all_ys.extend(ys)
            ax.scatter(all_xs, all_ys, s=60, c=team_colors.get(team_id, "gray"), label=f"Time {team_id}")


        ax.legend()
        frame_placeholder.pyplot(fig)
        plt.close(fig)


        # Pequeno delay para evitar travamento (mas sem travar pelo tempo do frame)
        # Garante sincronização com 30 FPS reais
        time.sleep(max(0, frame_interval - (time.perf_counter() - start_time - (current_time - min_time))))


else:
    time_selected = st.slider("Selecione o tempo (segundos):", float(min_time), float(max_time), float(min_time), step=0.1)
    frame_data = df_positions[np.isclose(df_positions["timestamp"], time_selected, atol=0.05)]

    fig, ax = plt.subplots(figsize=(10 * field_scale_x, 6 * field_scale_y))

    draw_field(ax, view=CAMERA_VIEW, show_lines=show_lines)

    for team_id, group in frame_data.groupby("team"):
        all_xs, all_ys = [], []
        for _, row in group.iterrows():
            xys = row["pts"]
            xs, ys = zip(*xys)
            all_xs.extend(xs)
            all_ys.extend(ys)
        ax.scatter(all_xs, all_ys, s=60, c=team_colors.get(team_id, "gray"), label=f"Time {team_id}")

    ax.legend()
    st.pyplot(fig)



# Gráficos de evolução tática - em linha única cada um, mais largos e achatados
st.subheader("Evolução das Métricas Táticas")


def to_rgba(color_name, alpha=0.3):
    """Converte nome CSS para string rgba usada pelo Plotly"""
    rgb = mcolors.to_rgb(color_name)
    return f"rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, {alpha})"

def plot_area_diff(df, y_column, title, y_label):
    fig = go.Figure()
    times = sorted(df["team"].unique())
    df1 = df[df["team"] == times[0]].sort_values("tempo")
    df2 = df[df["team"] == times[1]].sort_values("tempo")

    tempo = df1["tempo"].values
    y1 = df1[y_column].values
    y2 = df2[y_column].values

    # Adiciona as linhas dos times
    fig.add_trace(go.Scatter(
        x=tempo, y=y1,
        mode="lines",
        name=f"Time {times[0]}",
        line=dict(color=TEAM_COLORS_DASH[times[0]])
    ))

    fig.add_trace(go.Scatter(
        x=tempo, y=y2,
        mode="lines",
        name=f"Time {times[1]}",
        line=dict(color=TEAM_COLORS_DASH[times[1]])
    ))

    # Preencher por segmento (entre dois pontos consecutivos)
    for i in range(len(tempo)-1):
        x_seg = [tempo[i], tempo[i+1], tempo[i+1], tempo[i]]
        y_top = [max(y1[i], y2[i]), max(y1[i+1], y2[i+1])]
        y_bot = [min(y1[i], y2[i]), min(y1[i+1], y2[i+1])]
        y_seg = y_top + y_bot[::-1]

        # Decide cor localmente
        if (y1[i] + y1[i+1]) > (y2[i] + y2[i+1]):
            fill_color = to_rgba(TEAM_COLORS_DASH[times[0]])
        else:
            fill_color = to_rgba(TEAM_COLORS_DASH[times[1]])

        fig.add_trace(go.Scatter(
            x=x_seg,
            y=y_seg,
            mode="none",  # <-- evita desenhar linhas/pontos visuai
            fill="toself",
            fillcolor=fill_color,
            hoverinfo="skip",
            showlegend=False
            ))


    fig.update_layout(
        title=title,
        xaxis_title="Tempo (s)",
        yaxis_title=y_label,
        height=300,
        margin=dict(l=40, r=40, t=40, b=20)
    )
    return fig



# Gráfico 1 - Largura com área entre curvas
fig_largura = plot_area_diff(df_metrics, "largura", "Largura", "Largura")
st.plotly_chart(fig_largura, use_container_width=True)

# Gráfico 2 - Profundidade com área entre curvas
fig_profundidade = plot_area_diff(df_metrics, "profundidade", "Profundidade", "Profundidade")
st.plotly_chart(fig_profundidade, use_container_width=True)


# Gráfico 3 - Pressão
fig_pressao = px.line(
    df_metrics[df_metrics["pressao"] > 0],  # filtra valores válidos
    x="tempo",
    y="pressao",
    color="team",
    color_discrete_map=TEAM_COLORS_DASH,
    title="Pressão (apenas quando a bola é detectada)",
    labels={"tempo": "Tempo (s)", "pressao": "Pressão", "team": "Time"}
)
fig_pressao.update_traces(mode='lines+markers', line_shape='spline')
fig_pressao.update_layout(height=300, margin=dict(l=40, r=40, t=40, b=20))
fig_pressao.update_yaxes(range=[0, 1])
st.plotly_chart(fig_pressao, use_container_width=True)

