import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import matplotlib.dates as mdates
import plotly.express as px
import json
import requests
import plotly.graph_objects as go
import networkx as nx
from plotly.colors import qualitative

# ---------- REDES E GRAFOS

def redesGrafos(dataset):
    print("""

        Visualização de Redes e Grafos

        Grafo node-link
    """)

    # Grafo node-link

    dataset["date"] = pd.to_datetime(dataset["date"])
    ultimaData = dataset["date"].max()
    dadosAtuais = dataset[dataset["date"] == ultimaData]

    mortesPorEstado = dadosAtuais.groupby("state")["deaths"].max().reset_index()

    vizinhos = {
        "AC": ["RO", "AM"],
        "AL": ["SE", "BA", "PE"],
        "AP": ["PA"],
        "AM": ["RR", "PA", "MT", "RO", "AC"],
        "BA": ["SE", "AL", "PE", "PI", "GO", "MG", "ES"],
        "CE": ["RN", "PB", "PE", "PI"],
        "DF": ["GO", "MG"],
        "ES": ["BA", "MG", "RJ"],
        "GO": ["TO", "MG", "BA", "DF", "MT", "MS"],
        "MA": ["PI", "TO", "PA"],
        "MT": ["PA", "RO", "AM", "GO", "MS"],
        "MS": ["MT", "GO", "SP", "PR"],
        "MG": ["BA", "ES", "RJ", "SP", "DF", "GO"],
        "PA": ["RR", "AP", "MA", "TO", "MT", "AM"],
        "PB": ["RN", "CE", "PE"],
        "PR": ["SC", "SP", "MS"],
        "PE": ["PB", "CE", "BA", "AL"],
        "PI": ["MA", "CE", "BA"],
        "RJ": ["ES", "MG", "SP"],
        "RN": ["CE", "PB"],
        "RS": ["SC"],
        "RO": ["AC", "MT", "AM"],
        "RR": ["AM", "PA"],
        "SC": ["PR", "RS"],
        "SP": ["MG", "RJ", "PR", "MS"],
        "SE": ["AL", "BA"],
        "TO": ["MA", "PA", "GO"]
    }

    grafo = nx.Graph()

    for _, row in mortesPorEstado.iterrows():
        grafo.add_node(row["state"], deaths=row["deaths"])

    for estado, listaVizinhos in vizinhos.items():
        for vizinho in listaVizinhos:
            if grafo.has_node(estado) and grafo.has_node(vizinho):
                grafo.add_edge(estado, vizinho)

    pos = nx.spring_layout(grafo, k=0.5, iterations=50)

    arestaX, arestaY = [], []

    for aresta in grafo.edges():
        x0, y0 = pos[aresta[0]]
        x1, y1 = pos[aresta[1]]
        arestaX += [x0, x1, None]
        arestaY += [y0, y1, None]

    tracoAresta = go.Scatter(
        x=arestaX, y=arestaY,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines"
    )

    noX, noY, textoNo, tamanhoNo = [], [], [], []
    
    for no in grafo.nodes():
        x, y = pos[no]
        noX.append(x)
        noY.append(y)
        mortes = grafo.nodes[no]["deaths"]
        textoNo.append(f"{no}<br>Mortes: {mortes:,}")
        tamanhoNo.append(max(10, mortes / 2000))

    
    tracoNo = go.Scatter(
        x=noX, y=noY,
        mode="markers+text",
        textposition="bottom center",
        hoverinfo="text",
        marker=dict(
            showscale=True,
            colorscale="Reds",
            reversescale=False,
            color=[grafo.nodes[n]["deaths"] for n in grafo.nodes()],
            size=tamanhoNo,
            colorbar=dict(
                thickness=15,
                title="Mortes",
                xanchor="left"
            ),
            line_width=2
        ),
        text=list(grafo.nodes()),
        hovertext=textoNo
    )
        
    fig = go.Figure(data=[tracoAresta, tracoNo],
                    layout=go.Layout(
                        title=f"Mortes por COVID-19 por Estado até a última data registrada 27/03/2022 (Grafo Node-link)",
                        title_x=0.5,
                        showlegend=False,
                        hovermode="closest",
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    
    fig.show()

    # Diagrama de Cordas

    print("""
        Diagrama de Cordas
    """)

    estados = sorted(mortesPorEstado["state"].unique())
    indexEstados = {estado: i for i, estado in enumerate(estados)}
    mortesDict = dict(zip(mortesPorEstado["state"], mortesPorEstado["deaths"]))

    fonte, alvo, valor = [], [], []
    label = estados

    ligacoesAdicionadas = set()

    for origem, destinos in vizinhos.items():
        for destino in destinos:
            par = tuple(sorted([origem, destino]))
            if par not in ligacoesAdicionadas and origem in mortesDict and destino in mortesDict:
                ligacoesAdicionadas.add(par)
                fonte.append(indexEstados[origem])
                alvo.append(indexEstados[destino])
                mediaMortes = (mortesDict[origem] + mortesDict[destino]) / 2
                valor.append(mediaMortes)

    cores = qualitative.Set3
    coresRepetidas = (cores * ((len(label) // len(cores)) + 1))[:len(label)]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=label,
            color=coresRepetidas
        ),
        link=dict(
            source=fonte,
            target=alvo,
            value=valor,
            color="rgba(200,0,0,0.3)"
        )
    )])

    fig.update_layout(
        title_text="Mortes por COVID-19 entre os Estados Vizinhos - última data registrada 27/03/2022 (Diagrama de Cordas Sankey)",
        font_size=12
    )

    fig.show()
    

# ---------- GRÁFICOS DE INFORMAÇÃO HIERÁRQUICA

def informacaoHierarquica(dataset):
    print("""

        Visualização com gráfico de Informação Hierárquica

        Treemaps
    """)

    # Treemaps

    dataset["date"] = pd.to_datetime(dataset["date"])

    ultimaData = dataset["date"].max()
    dadosAtuais = dataset[dataset["date"] == ultimaData]

    mortesPorEstado = dadosAtuais.groupby("state")["deaths"].max().reset_index()

    estadoPorRegiao = {
        "AC": "Norte", "AL": "Nordeste", "AP": "Norte", "AM": "Norte", "BA": "Nordeste",
        "CE": "Nordeste", "DF": "Centro-Oeste", "ES": "Sudeste", "GO": "Centro-Oeste",
        "MA": "Nordeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "MG": "Sudeste",
        "PA": "Norte", "PB": "Nordeste", "PR": "Sul", "PE": "Nordeste", "PI": "Nordeste",
        "RJ": "Sudeste", "RN": "Nordeste", "RS": "Sul", "RO": "Norte", "RR": "Norte",
        "SC": "Sul", "SP": "Sudeste", "SE": "Nordeste", "TO": "Norte"
    }

    mortesPorEstado["região"] = mortesPorEstado["state"].map(estadoPorRegiao)

    fig = px.treemap(
        mortesPorEstado,
        path=["região", "state"],
        values="deaths",
        labels={"deaths": "Mortes"},
        color="deaths",
        color_continuous_scale="Reds",
        title=f"Mortes acumuladas por COVID-19 por Região e Estado até última data registrada 27/03/2022 (Treemaps)"
    )

    fig.update_traces(
        texttemplate="%{label}<br>%{value:,}",
        hovertemplate="<b>%{label}</b><br>Mortes: %{value:,}<extra></extra>"
    )
    
    fig.update_layout(title_x=0.5)
    fig.show()

    # Sunburst

    print("""
        Sunburst
    """)

    fig = px.sunburst(
        mortesPorEstado,
        path=["região", "state"],
        values="deaths",
        labels={"deaths": "Mortes"},
        color="deaths",
        color_continuous_scale="Reds",
        title=f"Mortes acumuladas por COVID-19 por Região e Estado até última data registrada 27/03/2022 (Sunburst)"
    )
    
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Mortes: %{value:,}<extra></extra>"
    )

    fig.update_layout(title_x=0.5)
    fig.show()
    

# ---------- GRÁFICO DE INFORMAÇÃO GEOGRÁFICA

def informacaoGeografica(dataset):
    print("""

        Visualização com gráfico de Informação Geográfica

        Mapa Coroplético (Choropleth Map)
    """)

    
    # Mapa Coroplético

    dataset["date"] = pd.to_datetime(dataset["date"])

    ultimaData = dataset["date"].max()
    dadosAtuais = dataset[dataset["date"] == ultimaData]

    mortesPorEstado = dadosAtuais.groupby("state")["deaths"].sum().reset_index()

    mortesPorEstado["state"] = mortesPorEstado["state"].str.upper()

    geojsonUrl = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojsonData = requests.get(geojsonUrl).json()

    todosEstados = [f["properties"]["sigla"].upper() for f in geojsonData["features"]]

    mortesPorEstado = mortesPorEstado.set_index("state").reindex(todosEstados, fill_value=0).reset_index()

    for feature in geojsonData["features"]:
        feature["id"] = feature["properties"]["sigla"].upper()

    fig = px.choropleth(
        mortesPorEstado,
        geojson=geojsonData,
        locations="state",
        featureidkey="properties.sigla",
        color="deaths",
        color_continuous_scale="Reds",
        scope="south america",
        labels={"deaths": "Mortes"},
        title="Total de Mortes por COVID-19 por Estado para a última data registrada 27/03/2022 (Mapa Coroplético)"
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="#f0f0f0"
    )

    fig.update_layout(title_x=0.5)
    fig.show()

# ---------- GRÁFICOS DE INFORMAÇÃO TEMPORAL

def informacaoTemporal(dataset):
    print("""

        Visualização com gráficos de Informação Temporal

        Gráfico de Gantt
    """)
    
    # Gráfico de Gantt 

    ultimaData = dataset["date"].max()
    dadosUltimaData = dataset[dataset["date"] == ultimaData]
    totalEstado = dadosUltimaData.groupby("state")["confirmed"].sum().reset_index()
    topEstados = totalEstado.sort_values("confirmed", ascending=False).head(10)["state"].tolist()

    dadosTopEstados = dataset[dataset["state"].isin(topEstados)]
    dadosTopEstadosAgrupado = dadosTopEstados.groupby(["state", "date"])["confirmed"].max().reset_index()
    dadosTopEstadosAgrupado["date"] = pd.to_datetime(dadosTopEstadosAgrupado["date"])
    dadosTopEstadosAgrupado = dadosTopEstadosAgrupado.sort_values(["state", "date"])

    fig, ax = plt.subplots(figsize=(14, 6))

    estados = dadosTopEstadosAgrupado["state"].unique()
    cores = plt.cm.tab10.colors

    for i, estado in enumerate(estados):
        dadosEstado = dadosTopEstadosAgrupado[dadosTopEstadosAgrupado["state"] == estado].reset_index(drop=True)


        inicio = dadosEstado["date"].iloc[0]
        fim = dadosEstado["date"].iloc[-1]
        casosTotais = dadosEstado["confirmed"].iloc[-1]

        numeroInicio = mdates.date2num(inicio)
        numeroFim = mdates.date2num(fim)
        duracao = numeroFim - numeroInicio

        ax.barh(i, duracao, left=numeroInicio, height=0.8, color=cores[i], alpha=0.8, edgecolor="none")
        ax.text(numeroFim + 10, i, f"{(casosTotais):,}",
                   va="center", fontsize=9, ha="left",
                   bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1),
                   zorder=10)

    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    
    ax.set_yticks(range(len(estados)))
    ax.set_yticklabels(estados)
    ax.set_xlabel("Data")
    ax.set_title("Evolução dos Casos confirmados de COVID-19 (Top 10 Estados) (Gantt)")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()

    # Gráfico de Linhas

    print("""
        Gráfico de Linhas
    """)

    plt.style.use("default")

    topEstados = dataset[dataset["date"] == ultimaData] \
                      .groupby("state")["deaths"] \
                      .sum().nlargest(5).index.tolist()
    
    dadosTopEstados = dataset[dataset["state"].isin(topEstados)]
    dadosAgrupados = dadosTopEstados.groupby(["state", "date"])["deaths"].max().reset_index()
    dadosAgrupados["date"] = pd.to_datetime(dadosAgrupados["date"])

    plt.figure(figsize=(10, 5))

    cores = ["tab:blue", "tab:red", "tab:green", "tab:orange", "tab:purple"]

    for i, estado in enumerate(topEstados):
        dadosEstado = dadosAgrupados[dadosAgrupados["state"] == estado]
        plt.plot(dadosEstado["date"],
                 dadosEstado["deaths"],
                 color=cores[i],
                 linewidth=1.5,
                 label=estado)

    plt.xlabel("Data")
    plt.ylabel("Mortes")
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    plt.title("Evolução temporal das mortes da COVID-19 nos 5 estados mais afetados (Linhas)")
    plt.xticks(rotation=45)
    plt.legend(fontsize=8)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.show()

# ---------- GRÁFICOS DA ESTATÍSTICA DESCRITIVA

def estatisticaDescritiva(dataset):
    print("""

        Visualização com gráficos da Estatística Descritiva

        Gráfico de Barra
    """)

    # Gráfico de Barra
    
    acumulado = dataset.groupby("state")[["confirmed", "deaths"]].max().reset_index()
    acumulado = acumulado.sort_values("confirmed", ascending=False)

    plt.figure(figsize=(14, 6))
    x = range(len(acumulado))
    largura = 0.4

    confirmados = plt.bar(
        [i - largura/2 for i in x],
        acumulado["confirmed"],
        width=largura,
        label="Casos Confirmados",
        color="steelblue"
    )

    mortes = plt.bar(
        [i + largura/2 for i in x],
        acumulado["deaths"],
        width=largura,
        label="Mortes",
        color="salmon"
    )

    for barra in confirmados:
        altura = barra.get_height()
        plt.text(barra.get_x() + barra.get_width()/2, altura + 1000, f"{int(altura):,}",
                 ha="center", va="bottom", fontsize=8, rotation=90)

    for barra in mortes:
        altura = barra.get_height()
        plt.text(barra.get_x() + barra.get_width()/2, altura + 1000, f"{int(altura):,}",
                 ha="center", va="bottom", fontsize=8, color="black", rotation=90)
    

    plt.xticks(x, acumulado["state"])
    plt.title("Total acumulado de casos confirmados e morte por estado de 19/06/2020 a 27/03/2022 (Barra)")
    plt.xlabel("Estado")
    plt.ylabel("Total")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    plt.tight_layout()
    plt.show()

    # Gráfico de Setores (pizza)

    print("""
        Gráfico de Setores
    """)

    ultimaData = dataset["date"].max()
    dadosUltimaData = dataset[dataset["date"] == ultimaData]
    totalPorEstado = dadosUltimaData.groupby("state")["confirmed"].sum().reset_index()
    totalPorEstado = totalPorEstado.sort_values("confirmed", ascending=False)

    topEstados = totalPorEstado.head(10)
    outros = totalPorEstado.iloc[10:]["confirmed"].sum()

    labels = list(topEstados["state"]) + ["Outros"]
    tamanhos = list(topEstados["confirmed"]) + [outros]

    coresTopEstados = plt.cm.tab20.colors[:10]
    corOutros = (0.6, 0.6, 0.6)

    cores = list(coresTopEstados) + [corOutros]

    plt.figure(figsize=(10, 8))
    plt.pie(
        tamanhos,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=cores,
        textprops={"fontsize": 9}
    )

    plt.title("10 estados com mais casos acumulados de COVID-19 e o resto do Brasil (Setores)")
    plt.axis("equal")
    plt.show()


# ---------- IMPLEMENTAÇÃO

def implementacao(dataset):
    graficos = ["estatistica_descritiva", "informacao_temporal", "informacao_geografica", "informacao_hierarquica", "redes_grafos"]
    for grafico in graficos:
        if grafico == "estatistica_descritiva":
            estatisticaDescritiva(dataset)
        if grafico == "informacao_temporal":
            informacaoTemporal(dataset)
        if grafico == "informacao_geografica":
            informacaoGeografica(dataset)
        if grafico == "informacao_hierarquica":
            informacaoHierarquica(dataset)
        if grafico == "redes_grafos":
            redesGrafos(dataset)


# ---------- LEITURA

def leitura():
    print("""
        Lendo arquivo dataset...
    """)

    dataset = pd.read_csv('caso.csv', parse_dates=["date"])
    return dataset

# ---------- MENU PRINCIPAL

def menu():
    print("""

        VISUALIZAÇÃO DA INFORMAÇÃO
        Dataset: Casos de COVID-19 no Brasil de 19/06/2020 a 27/03/2022

        1 - Visualização da Estatística Descritiva
            1.1 - Barra
            1.2 - Setores (pizza)
        2 - Visualização de Informação Temporal
            2.1 - Gantt
            2.2 - Linhas
        3 - Visualização de Informação Geográfica
            3.1 - Mapa Coroplético (Choropleth Map)
        4 - Visualização de Informação Hierárquica
            4.1 - Treemaps
            4.2 - Sunburst
        5 - Visualização de Redes e Grafos
            5.1 - Grafo node-link
            5.2 - Diagrama de cordas


        VAMOS INICIAR!!
    """)

    dataset = leitura()
    implementacao(dataset)

# ---------- MENU

menu()
