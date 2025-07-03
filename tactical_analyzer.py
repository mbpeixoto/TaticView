from sklearn.cluster import KMeans
import numpy as np
import cv2
import csv
import json
from config import CAMERA_VIEW, METRICS_CSV_PATH, POSITIONS_CSV_PATH


class TacticalAnalyzer:
    """
    Classe responsável por agrupar jogadores em times e linhas táticas,
    e calcular métricas defensivas (largura, profundidade, pressão).
    """

    def __init__(self, fps=30):
        self.k_teams = 2
        self.k_lines = 3
        self.fps = fps
        self.frame_count = 0

        self.csv_file = open(METRICS_CSV_PATH, mode="w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            "frame", "team", "largura", "profundidade", "pressao",
            "largura_linha_1", "largura_linha_2", "largura_linha_3",
            "profundidade_1_2", "profundidade_2_3"
        ])

        self.positions_file = open(POSITIONS_CSV_PATH, mode="w", newline="")
        self.positions_writer = csv.writer(self.positions_file)
        self.positions_writer.writerow(["frame", "team", "timestamp", "positions"])

    def extract_player_colors(self, frame, boxes):
        colors_rgb = []
        for (x, y, w, h) in boxes:
            x1 = max(int(x - w / 2), 0)
            y1 = max(int(y - h / 2), 0)
            x2 = min(int(x + w / 2), frame.shape[1])
            y2 = min(int(y + h / 2), frame.shape[0])
            patch = frame[y1:y2, x1:x2]
            mean_rgb = patch.mean(axis=(0, 1)) if patch.size > 0 else [0, 0, 0]
            colors_rgb.append(mean_rgb)
        return np.array(colors_rgb)

    def assign_team_ids_stable(self, cluster_means):
        brightness = [np.sum(c) for c in cluster_means]
        return np.argsort(brightness)

    def analyze(self, detections, frame_shape, frame):
        players = np.array(detections["players"])
        ball = np.array(detections["ball"]) if detections["ball"] is not None else None
        frame_width = frame_shape[1]

        boxes = [(x, y, 30, 30) for (x, y) in players]
        color_features = self.extract_player_colors(frame, boxes)

        team_model = KMeans(n_clusters=self.k_teams, n_init=10)
        if len(players) < 2:
            return {"ball": ball}
        team_labels = team_model.fit_predict(color_features)

        cluster_means = [np.mean(color_features[team_labels == i], axis=0) for i in range(self.k_teams)]
        internal_to_real_team = self.assign_team_ids_stable(cluster_means)

        result = {}

        for internal_id, team_index in enumerate(internal_to_real_team):
            team_pos = players[team_labels == team_index]

            base_axis = team_pos[:, 0].reshape(-1, 1) if CAMERA_VIEW == "side_view" else team_pos[:, 1].reshape(-1, 1)

            if len(base_axis) >= 3:
                line_model = KMeans(n_clusters=self.k_lines, random_state=42)
                line_labels = line_model.fit_predict(base_axis)
            else:
                line_labels = np.zeros(len(base_axis), dtype=int)

            valid_means, valid_indices = [], []
            for i in range(self.k_lines):
                group = base_axis[line_labels == i]
                if len(group) > 0:
                    valid_means.append(group.mean())
                    valid_indices.append(i)

            if len(valid_means) < 2:
                linhas = {"linha_1": team_pos}
            else:
                ordered = [valid_indices[i] for i in np.argsort(valid_means)]
                linhas = {
                    f"linha_{i+1}": team_pos[line_labels == label]
                    for i, label in enumerate(ordered)
                }

            largura_total = np.max(team_pos[:, 0]) - np.min(team_pos[:, 0])
            profundidade_total = np.max(team_pos[:, 1]) - np.min(team_pos[:, 1])

            if ball is not None and len(team_pos) > 0:
                dists = np.linalg.norm(team_pos - ball, axis=1)
                pesos = 1 / (dists + 1)
                pressao = np.mean(pesos) * 100
            else:
                pressao = 0.0

            largura_linhas = {}
            max_largura = frame_width
            for i in range(1, 4):
                nome = f"linha_{i}"
                if nome in linhas and len(linhas[nome]) > 0:
                    largura_pixel = linhas[nome][:, 0].max() - linhas[nome][:, 0].min()
                    intensidade = int(255 * largura_pixel / max_largura)
                    intensidade = max(30, min(intensidade, 255))
                    largura_linhas[nome] = {
                        "valor": float(largura_pixel / frame_width * 100),
                        "intensidade": intensidade
                    }
                else:
                    largura_linhas[nome] = {"valor": 0.0, "intensidade": 50}

            profundidades_linhas = {}
            for i in range(1, 3):
                nome1 = f"linha_{i}"
                nome2 = f"linha_{i+1}"
                if nome1 in linhas and nome2 in linhas and len(linhas[nome1]) > 0 and len(linhas[nome2]) > 0:
                    y1 = linhas[nome1][:, 1].mean()
                    y2 = linhas[nome2][:, 1].mean()
                    profundidades_linhas[f"{nome1}_{nome2}"] = abs(y2 - y1)
                else:
                    profundidades_linhas[f"{nome1}_{nome2}"] = 0.0

            self.csv_writer.writerow([
                self.frame_count, internal_id, largura_total, profundidade_total, pressao,
                largura_linhas["linha_1"]["valor"], largura_linhas["linha_2"]["valor"], largura_linhas["linha_3"]["valor"],
                profundidades_linhas["linha_1_linha_2"], profundidades_linhas["linha_2_linha_3"]
            ])

            timestamp = self.frame_count / self.fps
            self.positions_writer.writerow([
                self.frame_count, internal_id, timestamp, json.dumps(team_pos.tolist())
            ])

            result[internal_id] = {
                "positions": team_pos,
                "linhas": linhas,
                "metrics": {
                    "largura": largura_total,
                    "profundidade": profundidade_total,
                    "pressao": pressao,
                    "largura_linhas": largura_linhas,
                    "profundidades_linhas": profundidades_linhas
                }
            }

        self.frame_count += 1
        return result

    def __del__(self):
        if self.csv_file:
            self.csv_file.close()
        if self.positions_file:
            self.positions_file.close()
