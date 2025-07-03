
# 🧠 Tatic View - Análise Tática Futebol

Este projeto realiza **análise tática defensiva em vídeos de partidas de futebol**, utilizando visão computacional com YOLO, agrupamento com KMeans, e visualização interativa via Streamlit e matplotlib.

---

## 📂 Estrutura do Projeto

```
├── main.py                 # Processa o vídeo, detecta jogadores e gera métricas (salva em CSV)
├── app.py                  # Dashboard interativo com Streamlit
├── run_all.py              # Executa o pipeline completo: processa o vídeo e abre o dashboard
├── config.py               # Arquivo central de configuração (caminhos, cores, visão da câmera)
│
├── detector.py             # Classe para carregar o modelo YOLO e detectar jogadores e bola
├── tactical_analyzer.py    # Cálculo de largura, profundidade, pressão, agrupamentos por linhas
├── visualizer.py           # Desenho dos jogadores, linhas, bola e métricas nos frames
│
├── uploads/
│   └── input.mp4           # Vídeo de entrada enviado pelo frontend ou salvo manualmente
│
├── outputs/
│   └── output_annotated.avi # Vídeo de output com anotações visuais
│
├── data/
│   ├── tactical_metrics.csv # Métricas táticas por frame (largura, profundidade, pressão)
│   └── positions.csv         # Posições 2D dos jogadores e bola por frame
│
└── requirements.txt         # Dependências do projeto (YOLO, OpenCV, Streamlit, etc.)
```

---

## ▶ Como Rodar o Projeto

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Rode o processamento do vídeo
```bash
python main.py
```

Isso irá:
- Processar `input.mp4`
- Detectar jogadores e bola com YOLO
- Gerar `output_annotated.avi`
- Salvar métricas em `tactical_metrics.csv` e posições em `positions.csv`

### 3. Execute o dashboard
```bash
streamlit run app.py
```

---

## 🧠 Lógica da Análise Tática

### 1. 🎯 Largura Total
A **largura** de um time é calculada como:
```python
largura = max_x - min_x
```
- `x` representa a coordenada **horizontal** (lateral do campo).
- É aplicada separadamente para cada time.

### 2. ⬇️ Profundidade Total
A **profundidade** de um time é a distância entre o jogador mais recuado e o mais avançado:
```python
profundidade = max_y - min_y
```
- `y` representa a coordenada **vertical**, ou seja, a **direção do gol**.

### 3. 📏 Largura por Linha (Defesa, Meio, Ataque)
Usamos KMeans para segmentar os jogadores em **3 linhas** por time.
Para cada linha:
```python
largura_linha = max_x - min_x
```

### 4. 🪜 Profundidade Entre Linhas
Calculamos a **distância média Y** entre as linhas:
```python
profundidade_def_meio = média_y_meio - média_y_defesa
profundidade_meio_ataque = média_y_ataque - média_y_meio
```

### 5. 🎯 Nível de Pressão
Se a bola foi detectada, a pressão é a **média da distância** entre a bola e as linhas do time **sem posse**:
```python
pressao = média das distâncias da bola até cada linha do time
```
- Normalizada entre `0` e `1` para visualização.
- Quando a bola não é detectada, a pressão é `0`.

---

## 📊 Dashboard

O app em Streamlit exibe:
- Campo 2D com movimentação animada dos jogadores
- Gráficos:
  - **Largura** por time
  - **Profundidade** por time
  - **Pressão** ao longo do tempo (quando bola detectada)

---

## ✅ Requisitos (`requirements.txt`)

```txt
opencv-python
numpy
pandas
matplotlib
scikit-learn
ultralytics
ultralyticsplus
streamlit
plotly
```

---

## 📌 Observações

- Observar e adaptar configurações em config.py

---
