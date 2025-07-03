# Importa dois tipos de modelo YOLO: local (ultralytics) e hospedado (Hugging Face)
from ultralytics import YOLO as LocalYOLO
from ultralyticsplus import YOLO as HFYOLO

class ObjectDetector:
    """
    Classe responsável por detectar jogadores e bola em frames de vídeo
    usando modelos YOLO (local ou do Hugging Face).
    """

    def __init__(self, model_type="local"):
        """
        Inicializa o detector com o tipo de modelo especificado.
        
        Parâmetros:
        - model_type (str): "huggingface" ou "local"
        """
        if model_type == "huggingface":
            # Usa modelo pré-treinado específico para futebol (mais preciso)
            self.model = HFYOLO("uisikdag/yolo-v8-football-players-detection")
        else:
            # Usa modelo genérico local YOLOv8n
            self.model = LocalYOLO("best.pt")

        # Mapeamento de índices de classe para nomes (ex: 0 -> "player")
        self.names = self.model.names

    def detect(self, frame, conf_threshold=0.7):
        """
        Detecta jogadores e bola no frame fornecido.

        Parâmetros:
        - frame (np.ndarray): imagem do vídeo
        - conf_threshold (float): limite de confiança para manter as detecções

        Retorno:
        - dict: {"players": [(x, y), ...], "ball": (x, y) or None}
        """
        # Realiza a predição
        results = self.model.predict(frame)[0]

        players = []
        ball = None

        # Percorre cada bounding box detectado
        for box in results.boxes:
            # Ignora detecções com confiança abaixo do limiar
            if box.conf[0] < conf_threshold:
                continue

            # Obtém classe e coordenadas da caixa
            cls = int(box.cls[0])
            label = self.names[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Calcula o centro da caixa (útil para visualizações e análise tática)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Filtra por tipo de objeto
            if label == "player":
                players.append((cx, cy))
            elif label == "ball":
                ball = (cx, cy)

        return {
            "players": players,
            "ball": ball
        }
