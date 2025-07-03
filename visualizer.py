import cv2
import numpy as np
from config import TEAM_COLORS, BALL_COLOR


class TacticalVisualizer:
    """
    Classe responsável por desenhar visualmente:
    - Os jogadores e suas linhas (defesa/meio/ataque)
    - A bola
    - As métricas táticas no canto da tela
    """

    def __init__(self):
        # Cores atribuídas a cada time (ID → RGB BGR)
        self.team_colors = TEAM_COLORS

    def draw_teams_and_lines(self, frame, analysis):
        frame_copy = frame.copy()

        for team_id, team_data in analysis.items():
            if team_id == "ball":
                continue  # ignora o item especial "ball"

            circle_color = self.team_colors.get(team_id, (255, 255, 255))  # fallback branco

            # --- Desenha polígono geral do time (envolve todos os jogadores do time) ---
            team_positions = team_data["positions"]
            if len(team_positions) >= 3:
                pts = np.array(team_positions, dtype=np.int32)
                hull = cv2.convexHull(pts)
                overlay_color = self.team_colors.get(team_id, (200, 200, 200))
                overlay = frame_copy.copy()
                cv2.drawContours(overlay, [hull], -1, overlay_color, thickness=cv2.FILLED)
                # Aplica transparência entre o overlay e o frame_copy
                alpha = 0.2
                frame_copy = cv2.addWeighted(overlay, alpha, frame_copy, 1 - alpha, 0)

            for linha_nome, jogadores in team_data["linhas"].items():
                info_linha = team_data["metrics"]["largura_linhas"].get(linha_nome, {})
                intensidade = info_linha.get("intensidade", 100)
                base_color = np.array(self.team_colors.get(team_id, (200, 200, 200)), dtype=np.uint8)
                cor_linha = tuple(int(c) for c in (base_color * (intensidade / 255)))

                for (x, y) in jogadores:
                    cv2.circle(frame_copy, (int(x), int(y)), 6, circle_color, -1)

                if len(jogadores) > 1:
                    sorted_players = sorted(jogadores, key=lambda p: p[0])
                    for i in range(len(sorted_players) - 1):
                        p1 = tuple(map(int, sorted_players[i]))
                        p2 = tuple(map(int, sorted_players[i + 1]))
                        cv2.line(frame_copy, p1, p2, cor_linha, 2)

        # Desenha a bola (amarelo)
        if "ball" in analysis and analysis["ball"] is not None:
            bx, by = map(int, analysis["ball"])
            cv2.circle(frame_copy, (bx, by), 6, BALL_COLOR, -1)

        return frame_copy

    def draw_metrics(self, frame, analysis):
        """
        Desenha as métricas táticas (largura, profundidade, pressão) no canto do frame.
        """
        y_offset = 20
        x_offset = 10
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        metric_colors = TEAM_COLORS

        for team_id, team_data in analysis.items():
            if not isinstance(team_id, int):  # ignora a bola
                continue

            metrics = team_data["metrics"]
            color = metric_colors.get(team_id, (255, 255, 255))

            texto = (
                f"Time {team_id}: Largura: {metrics['largura']:.1f}px, "
                f"Profundidade: {metrics['profundidade']:.1f}px, "
                f"Pressao: {metrics['pressao']:.1f}"
            )
            cv2.putText(frame, texto, (x_offset, y_offset), font, font_scale, color, thickness)
            y_offset += 18

            for linha, info in metrics.get("largura_linhas", {}).items():
                largura = info["valor"]
                cv2.putText(frame, f"{linha} largura: {largura:.1f}%", (x_offset + 20, y_offset), font, font_scale, color, thickness)
                y_offset += 18

            for nome, prof in metrics.get("profundidades_linhas", {}).items():
                cv2.putText(frame, f"{nome} profundidade: {prof:.1f}px", (x_offset + 20, y_offset), font, font_scale, color, thickness)
                y_offset += 18

        return frame
