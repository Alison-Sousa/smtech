import streamlit as st
import requests
import json
import pandas as pd
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

st.set_page_config(layout="wide", page_title="Buscador Acadêmico Inteligente")

def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def call_gemini_search(user_query, api_key):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    start_year = datetime.now().year - 10
    
    system_prompt = f"""
    Você é um assistente de pesquisa acadêmica de elite.
    1. Encontre 5 a 7 artigos acadêmicos revisados por pares (peer-reviewed) sobre a consulta do usuário.
    2. FILTRO CRÍTICO: Você NÃO DEVE incluir resultados de servidores de preprints (arxiv.org, biorxiv.org, medrxiv.org), repositórios (SSRN, MPRA, ResearchGate, Academia.edu) ou sites gerais (Wikipedia, jornais, blogs).
    3. PRIORIZE: Busque ativamente resultados de periódicos de alto impacto e editoras acadêmicas confiáveis (ex: Nature, Science, Cell, The Lancet, NEJM, AER, QJE, Elsevier, Springer, Wiley, Taylor & Francis, IEEE, ACM, jornais de sociedades científicas).
    4. FORMATO: Gere um objeto JSON com uma única chave "articles" contendo uma lista. Cada item da lista deve ser um objeto com: "title" (string), "authors" (lista de strings), "journal" (string), "year" (int), "abstract" (string), "keywords" (lista de strings), "url" (string), "isOpenAccess" (bool).
    5. IMPORTANTE: Retorne APENAS o código JSON puro, começando com {{ e terminando com }}. Não adicione "```json" ou qualquer outro texto.
    6. LIMITE DE TEMPO: Foque-se estritamente em artigos publicados nos últimos 10 anos (a partir de {start_year} até o presente).
    """
    
    payload = {
        "contents": [{"parts": [{"text": f"Encontre artigos acadêmicos sobre: {user_query}"}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
        # Removido o generationConfig que causava o erro 400
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        session = create_retry_session()
        response = session.post(api_url, headers=headers, data=json.dumps(payload), timeout=120)
        response.raise_for_status() 
        
        result = response.json()
        
        content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
        
        # Lógica de parsing robusta para extrair o JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            st.error(f"A API não retornou um JSON válido. Resposta: {content}")
            return None
            
        json_str = content[json_start:json_end]
        
        data = json.loads(json_str)
        return data.get('articles', [])
        
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro HTTP: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"Erro de Conexão: {req_err}")
    except json.JSONDecodeError:
        st.error(f"Erro ao decodificar a resposta da API. Resposta recebida: {content}")
    except Exception as e:
        st.error(f"Um erro inesperado ocorreu: {e}")
        
    return None

st.sidebar.title("Configuração")
api_key_input = st.sidebar.text_input("Sua Chave de API Gemini", type="password")

api_key = api_key_input
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

if not api_key:
    st.sidebar.warning("Insira sua API Key Gemini para começar.")
    st.info("Por favor, insira sua chave de API Gemini na barra lateral esquerda para ativar a busca.")
    st.stop()

st.title("Buscador de Artigos Acadêmicos 🧠")
st.markdown("Focado em periódicos de alto impacto. Pré-prints e repositórios são filtrados pela IA.")

query = st.text_input("Digite seu tópico de pesquisa...", value="inflação na Coreia do Sul e política monetária")
search_button = st.button("Buscar Artigos", type="primary")

if "results" not in st.session_state:
    st.session_state.results = None

if search_button and query:
    with st.spinner("Buscando, analisando e filtrando artigos... Isso pode levar um momento."):
        st.session_state.results = call_gemini_search(query, api_key)

if st.session_state.results is not None:
    if not st.session_state.results:
        st.warning("Nenhum artigo de alto impacto encontrado para este tópico, ou a API não conseguiu filtrar os resultados. Tente refinar sua busca.")
    else:
        try:
            df = pd.DataFrame(st.session_state.results)
            
            df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(1900).astype(int)
            df['isOpenAccess'] = df['isOpenAccess'].fillna(False).astype(bool)

            st.sidebar.divider()
            st.sidebar.header("Filtros")

            current_year = datetime.now().year
            min_year = int(df['year'].min()) if df['year'].min() > 1900 else 1980
            max_year = int(df['year'].max()) if df['year'].max() <= current_year else current_year
            
            if min_year >= max_year:
                year_range = (min_year, max_year)
            else:
                year_range = st.sidebar.slider(
                    "Filtrar por Ano de Publicação",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year)
                )

            oa_filter = st.sidebar.checkbox("Apenas Open Access", value=False)
            
            journal_list = sorted(df['journal'].unique().tolist())
            selected_journals = st.sidebar.multiselect("Filtrar por Journal", options=journal_list, default=journal_list)

            filtered_df = df.copy()
            if year_range[0] < year_range[1]:
                filtered_df = filtered_df[
                    (filtered_df['year'] >= year_range[0]) & 
                    (filtered_df['year'] <= year_range[1])
                ]
            
            if oa_filter:
                filtered_df = filtered_df[filtered_df['isOpenAccess'] == True]
                
            if selected_journals:
                filtered_df = filtered_df[filtered_df['journal'].isin(selected_journals)]

            st.subheader(f"{len(filtered_df)} resultados filtrados")
            
            for index, row in filtered_df.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        st.markdown(f"### {row['title']}")
                    with col2:
                        st.markdown(f"**{row['journal']}**")
                        st.markdown(f"**Ano:** {row['year']}")
                        if row['isOpenAccess']:
                            st.caption("🔓 Open Access")
                        
                    st.markdown(f"**Autores:** {', '.join(row['authors'] if row['authors'] else ['N/A'])}")
                    
                    if 'keywords' in row and row['keywords']:
                         st.markdown(f"**Palavras-chave:** *{', '.join(row['keywords'])}*")
                    
                    with st.expander("Ver Resumo (Abstract)"):
                        st.write(row['abstract'] if row['abstract'] else "Resumo não disponível.")
                    
                    st.link_button("Visitar Página do Artigo ↗️", row['url'], help=row['url'])

        except Exception as e:
            st.error(f"Erro ao processar os resultados: {e}")
            st.json(st.session_state.results)