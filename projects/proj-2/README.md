# 🧠 Buscador de Artigos Acadêmicos

Aplicativo que utiliza IA, API Gemini e a ferramenta de Google Search para encontrar artigos acadêmicos revisados por pares, com foco em publicações de alto impacto.

![Demo do App](app.gif)


## 🔎 Funcionalidades

* **Busca Inteligente:** Utiliza a API Gemini (`gemini-2.5-flash-preview-09-2025`) para processar a consulta do usuário.
* **Filtragem:** O prompt da API é instruído a:
    * Excluir pré-prints e repositórios.
    * Priorizar periódicos de alto impacto (Nature, Science, Elsevier, Springer, IEEE, etc.).
    * Focar em artigos dos últimos 10 anos.
    * Retornar uma lista estruturada em JSON.
* **Interface Interativa:**
    * Entrada segura de API Key na barra lateral (lê de `st.secrets` ou entrada manual).
    * Exibição dos resultados em cartões (`st.container`).
    * Resumo (abstract) expansível (`st.expander`).
    * Link direto para a página do artigo (`st.link_button`).
* **Filtros Pós-Busca:** Após a busca, a barra lateral exibe filtros para refinar os resultados por:
    * Intervalo de Ano de Publicação
    * Apenas "Open Access"
    * Periódico (Journal)
* **Eficiente:** Inclui lógica de *retry* (tentativas automáticas) para chamadas de API, tratando erros comuns de conexão ou servidor (500, 502, 503, 504).

## ⚙️ Como Funciona

1.  **Autenticação:** O usuário insere sua chave de API Gemini na barra lateral. O app também verifica o `st.secrets` para implantações.
2.  **Consulta:** O usuário digita um tópico de pesquisa (ex: "inflação na Coreia do Sul e política monetária").
3.  **Chamada de API:** O app envia a consulta e o *prompt de sistema* detalhado para a API Gemini, solicitando o uso da ferramenta `Google Search`.
4.  **Parsing:** A resposta da API, que deve ser um JSON, é extraída e validada.
5.  **Exibição:** Os dados são carregados em um DataFrame Pandas, e os filtros são gerados com base nos resultados.
6.  **Interação:** Os resultados são exibidos em cartões, permitindo ao usuário filtrar e explorar os resumos e links.

## 🛠️ Tecnologias Utilizadas

* **Python 3.10+**
* **Streamlit:** Para a interface web e componentes.
* **Pandas:** Para manipulação e filtragem dos dados.
* **Requests:** Para chamadas HTTP à API, com política de `Retry`.
* **Google Gemini API:** Para a funcionalidade de busca e filtragem.

## 🚀 Execução

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DO_DIRETORIO]
    ```

2.  **Crie um ambiente virtual e instale as dependências:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    pip install streamlit pandas requests
    ```

3.  **Configure sua API Key (Recomendado):**
    Crie um arquivo em `.streamlit/secrets.toml` e adicione sua chave:
    ```toml
    GEMINI_API_KEY = "SUA_CHAVE_GEMINI_AQUI"
    ```
    *Como alternativa, você pode inseri-la diretamente na interface do app.*

4.  **Execute o aplicativo:**
    ```bash
    streamlit run app.py
    ```