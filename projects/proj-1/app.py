import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

# Configuração inicial
st.set_page_config(layout="wide")
st.title("📊 Painel")

# ========================
# FUNÇÕES DE BUSCA DE DADOS
# ========================

@st.cache_data(ttl=3600)
def load_data(source):
    """Carrega países e indicadores disponíveis"""
    try:
        if source == "FMI":
            countries_url = "https://www.imf.org/external/datamapper/api/v1/countries"
            indicators_url = "https://www.imf.org/external/datamapper/api/v1/indicators"
            
            countries_res = requests.get(countries_url).json()
            indicators_res = requests.get(indicators_url).json()
            
            countries = {k: v['label'] for k, v in countries_res['countries'].items()}
            indicators = {k: v['label'] for k, v in indicators_res['indicators'].items()}
            
        else:  # Banco Mundial
            countries_url = "http://api.worldbank.org/v2/country?format=json&per_page=300"
            indicators_url = "http://api.worldbank.org/v2/indicator?format=json&per_page=20000"
            
            countries_res = requests.get(countries_url).json()[1]
            indicators_res = requests.get(indicators_url).json()[1]
            
            countries = {item['id']: item['name'] for item in countries_res}
            indicators = {item['id']: item['name'] for item in indicators_res}
            
        return countries, indicators
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}

def fetch_data(source, country, indicator, start, end):
    """Busca dados específicos da API selecionada"""
    try:
        if source == "FMI":
            url = f"https://www.imf.org/external/datamapper/api/v1/data/{indicator}/{country}/{start}/{end}"
            data = requests.get(url).json()
            values = data.get("values", {}).get(indicator, {}).get(country, {})
            df = pd.DataFrame(list(values.items()), columns=["year", "value"])
        else:
            url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date={start}:{end}&format=json"
            data = requests.get(url).json()[1]
            df = pd.DataFrame([(d['date'], d['value']) for d in data if d['value'] is not None], 
                           columns=["year", "value"])
        
        df["year"] = pd.to_numeric(df["year"])
        return df.dropna(), url
        
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame(), ""

# ========================
# FUNÇÕES DE MACHINE LEARNING (APENAS PARA BANCO MUNDIAL)
# ========================

def prever_tendencia(df, anos_previsao=3):
    """Previsão usando regressão polinomial (APENAS para Banco Mundial)"""
    try:
        # Garantir que os dados estão ordenados por ano
        df = df.sort_values('year')
        
        # Pegar apenas os últimos 10 anos para a previsão
        df_recente = df[df['year'] >= df['year'].max() - 10]
        
        X = df_recente['year'].values.reshape(-1, 1)
        y = df_recente['value'].values
        
        # Modelo de regressão polinomial
        model = make_pipeline(PolynomialFeatures(2), LinearRegression())
        model.fit(X, y)
        
        # Gerar apenas anos FUTUROS para previsão
        ultimo_ano = df['year'].max()
        future_years = np.arange(ultimo_ano + 1, ultimo_ano + anos_previsao + 1).reshape(-1, 1)
        future_pred = model.predict(future_years)
        
        # Criar DataFrame com previsões
        previsao_df = pd.DataFrame({
            'year': future_years.flatten(),
            'value': future_pred,
            'tipo': 'Previsão'
        })
        
        # Adicionar os dados reais (últimos 5 anos) para contexto
        dados_reais = df[df['year'] >= ultimo_ano - 5].copy()
        dados_reais['tipo'] = 'Dado Real'
        
        return pd.concat([dados_reais, previsao_df]).sort_values('year')
        
    except Exception as e:
        st.error(f"Erro na previsão: {e}")
        return None

def detectar_anomalias(df):
    """Detecta anos com valores anômalos (para ambas fontes)"""
    try:
        clf = IsolationForest(contamination=0.1, random_state=42)
        valores = df['value'].values.reshape(-1, 1)
        df['anomalia'] = clf.fit_predict(valores)
        return df[df['anomalia'] == -1]
    except:
        return pd.DataFrame()

def analisar_tendencia(df):
    """Análise de tendência (para ambas fontes)"""
    try:
        X = df['year'].values.reshape(-1, 1)
        y = df['value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        return {
            'coeficiente': model.coef_[0],
            'intercept': model.intercept_,
            'tendencia': 'Crescente' if model.coef_[0] > 0 else 'Decrescente'
        }
    except:
        return None

# ========================
# INTERFACE PRINCIPAL
# ========================

def main():
    st.sidebar.image("image.png", use_container_width=True)
    source = st.sidebar.radio("Fonte:", ["FMI", "Banco Mundial"], horizontal=True)
    
    # Carrega dados
    countries, indicators = load_data(source)
    
    if not countries or not indicators:
        st.error("Falha ao carregar dados. Tente novamente mais tarde.")
        return
    
    # Filtros
    col1, col2 = st.sidebar.columns(2)
    with col1:
        country = st.selectbox("País", options=list(countries.keys()), format_func=lambda x: countries[x])
    with col2:
        indicator = st.selectbox("Indicador", options=list(indicators.keys()), format_func=lambda x: indicators[x])
    
    year_range = st.sidebar.slider("Período", 1960, 2024, (2000, 2024))
    
    # Opções de ML (APENAS previsão para Banco Mundial)
    with st.sidebar.expander("⚙️ Análises Avançadas"):
        if source == "Banco Mundial":
            fazer_previsao = st.checkbox("Prever próximos 3 anos (linha vermelha)")
        else:
            fazer_previsao = False
            
        analise_tendencia = st.checkbox("Calcular tendência")
        detectar_outliers = st.checkbox("Identificar valores atípicos")

    if st.sidebar.button("▶️ Executar Análise", type="primary"):
        with st.spinner("Processando dados..."):
            df, api_url = fetch_data(source, country, indicator, year_range[0], year_range[1])
            
            if not df.empty:
                # Gráfico principal
                fig = px.line(df, x="year", y="value", 
                            title=f"{indicators[indicator]} - {countries[country]} ({source})",
                            markers=True)
                
                # Adicionar previsão APENAS para Banco Mundial
                if fazer_previsao and source == "Banco Mundial":
                    previsao_df = prever_tendencia(df)
                    if previsao_df is not None:
                        # Plotar dados reais
                        fig.add_scatter(
                            x=previsao_df[previsao_df['tipo']=='Dado Real']['year'],
                            y=previsao_df[previsao_df['tipo']=='Dado Real']['value'],
                            mode='lines+markers', 
                            name='Dados Reais (últimos anos)',
                            line=dict(color='blue')
                        )
                        
                        # Plotar previsão (LINHA VERMELHA)
                        fig.add_scatter(
                            x=previsao_df[previsao_df['tipo']=='Previsão']['year'],
                            y=previsao_df[previsao_df['tipo']=='Previsão']['value'],
                            mode='lines+markers', 
                            name='Previsão',
                            line=dict(dash='dot', color='red')
                        )
                        
                        # Linha divisória
                        ultimo_ano_real = df['year'].max()
                        fig.add_vline(
                            x=ultimo_ano_real, 
                            line_dash="dash", 
                            line_color="green", 
                            annotation_text="Último dado disponível"
                        )
                
                st.plotly_chart(fig, use_container_width=True)

                # Seção de análises
                if analise_tendencia or detectar_outliers:
                    st.subheader("🔍 Resultados das Análises")
                    
                    cols = st.columns(2)
                    
                    if analise_tendencia:
                        with cols[0]:
                            st.markdown("**📈 Tendência**")
                            tendencia = analisar_tendencia(df)
                            if tendencia:
                                st.metric("Direção", tendencia['tendencia'])
                                st.metric("Taxa anual", f"{tendencia['coeficiente']:.2f}")
                                st.metric("Valor base (ano 0)", f"{tendencia['intercept']:.2f}")
                    
                    if detectar_outliers:
                        with cols[1]:
                            st.markdown("**⚠️ Anos Atípicos**")
                            anomalias = detectar_anomalias(df)
                            if not anomalias.empty:
                                st.write("Anos com valores incomuns:")
                                st.dataframe(anomalias[['year', 'value']].style.highlight_max(color='red'))
                            else:
                                st.write("Nenhum valor atípico significativo encontrado")
                
                # Fonte e download
                st.markdown(f"**Fonte dos dados:** [{source}]({api_url})")
                csv = df.to_csv(index=False)
                st.download_button("📥 Exportar CSV", csv, 
                                 f"dados_{source}_{country}_{indicator}.csv",
                                 "text/csv")
            else:
                st.warning("Não foram encontrados dados para os parâmetros selecionados")

if __name__ == "__main__":
    main()