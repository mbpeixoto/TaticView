# config.py

# Caminhos de entrada e saída
INPUT_VIDEO_PATH = "./uploads/input.mp4"  # ou detectado automaticamente
OUTPUT_VIDEO_PATH = "outputs/output_annotated.avi"

# Pasta de dados
METRICS_CSV_PATH = "data/tactical_metrics.csv"
POSITIONS_CSV_PATH = "data/positions.csv"

# Cores dos times BGR
TEAM_COLORS = {
    0: (255, 0, 0), # azul
    1: (0, 255, 255), # amarelo
}
BALL_COLOR = (0, 0, 255) # vermelho

# Cores para uso em Plotly e Matplotlib (string CSS ou "rgb(r,g,b)")
TEAM_COLORS_DASH = {
    0: "blue",
    1: "yellow"
}
BALL_COLOR_DASH = "red"



# Modelo e visão
YOLO_MODEL_TYPE = "local"
CAMERA_VIEW = "behind_goal" #behind_goal ou side_view
DEFAULT_FPS = 30

