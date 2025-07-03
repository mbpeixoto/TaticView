import cv2
from detector import ObjectDetector
from tactical_analyzer import TacticalAnalyzer, CAMERA_VIEW
from visualizer import TacticalVisualizer
from config import INPUT_VIDEO_PATH, OUTPUT_VIDEO_PATH, YOLO_MODEL_TYPE

# === Inicialização dos componentes principais ===

# Inicializa o detector (modelo YOLO local ou Hugging Face)
detector = ObjectDetector(model_type=YOLO_MODEL_TYPE)

# Inicializa o visualizador para desenhar informações no vídeo
visualizer = TacticalVisualizer()

# Caminhos dos arquivos de entrada e saída

input_video_path = INPUT_VIDEO_PATH
output_video_path = OUTPUT_VIDEO_PATH


# === Leitura do vídeo de entrada ===

cap = cv2.VideoCapture(input_video_path)

# Coleta o número de frames por segundo (FPS) do vídeo
fps = cap.get(cv2.CAP_PROP_FPS)



# Obtém informações sobre o vídeo
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
if fps == 0:
    raise ValueError("FPS do vídeo é 0. Verifique se o vídeo foi carregado corretamente.")

print(f"Vídeo original: {frame_count} frames a {fps:.2f} FPS → {frame_count / fps:.2f} segundos")

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Inicializa o analisador tático com base no FPS
analyzer = TacticalAnalyzer(fps=fps)

print(f"Vídeo original: {frame_count} frames a {fps:.2f} FPS → {frame_count / fps:.2f} segundos")

# === Prepara o vídeo de saída ===

# Define o codec (XVID gera AVI, compatível com muitos players)
fourcc = cv2.VideoWriter_fourcc(*'XVID')

# Inicializa o escritor de vídeo com as dimensões e FPS do original
video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# === Loop de processamento frame a frame ===

frame_id = 0
frames_salvos = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # Fim do vídeo

    # === Etapa 1: Detecção com YOLO ===
    detections = detector.detect(frame, conf_threshold=0.4)

    if detections["players"]:
        # === Etapa 2: Análise Tática ===
        analysis = analyzer.analyze(detections, frame.shape, frame)

        # Se bola foi detectada, adiciona no dicionário da análise
        if detections["ball"]:
            analysis["ball"] = detections["ball"]

        # === Etapa 3: Visualização e Anotações no Frame ===
        frame_annotated = visualizer.draw_teams_and_lines(frame, analysis)
        frame_annotated = visualizer.draw_metrics(frame_annotated, analysis)

        # === Etapa 4: Escreve frame anotado no vídeo de saída ===
        video_writer.write(frame_annotated)
        frames_salvos += 1

    frame_id += 1

# === Liberação de recursos ===

cap.release()
video_writer.release()

# === Verificação do vídeo de saída ===

cap_out = cv2.VideoCapture(output_video_path)
out_fps = cap_out.get(cv2.CAP_PROP_FPS)
out_frames = cap_out.get(cv2.CAP_PROP_FRAME_COUNT)

if out_fps > 0:
    print(f"Vídeo gerado: {out_frames:.0f} frames a {out_fps:.2f} FPS → {out_frames / out_fps:.2f} segundos")
else:
    print("⚠️ Erro ao ler FPS do vídeo de saída. Arquivo pode estar corrompido.")

cap_out.release()
