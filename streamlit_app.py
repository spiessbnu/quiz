import streamlit as st
import random
import os
# Reativando a importação do web_rag
from backend.utils import (
    generate_quiz,
    get_closed_book_answers,
    get_web_rag_answers_and_snippets,
)

# Configuração da página
st.set_page_config(
    page_title="Quiz",
    page_icon="🧑‍🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .quiz-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .result-correct {
        color: #28a745;
        font-weight: bold;
    }
    .result-wrong {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho principal
st.markdown("""
<div class="main-header">
    <h1>🧑‍🏫 Quiz</h1>
    <p style="font-size: 1.2rem;">O sistema gera um quiz a partir de uma URL. Você pode jogar o quiz, ou deixar a LLM jogar.</p>
    <p><strong>Construído com: 🏗️ Haystack • 🤖 GPT-4o-mini • ⚡ OpenAI</strong></p>
</div>
""", unsafe_allow_html=True)

# URLs de exemplo
URL_EXAMPLES = [
    "https://pt.wikipedia.org/wiki/Fra%C3%A7%C3%A3o",
    "https://en.wikipedia.org/wiki/Predator_(film)",
    "https://lite.cnn.com/2024/04/22/entertainment/zendaya-challengers-interview/index.html",
    "https://en.wikipedia.org/wiki/The_Cure",
    "https://en.wikipedia.org/wiki/Masters_of_Doom",
    "https://www.rainforest-alliance.org/species/howler-monkey/",
    "https://lite.cnn.com/2024/05/23/travel/star-wars-hotel-disney-jenny-nicholson-cec/index.html",
    "https://en.wikipedia.org/wiki/Indiana_Jones_(character)",
    "https://www.rainforest-alliance.org/species/river-dolphin/",
    "https://www.rainforest-alliance.org/species/sloth/",
]

# Inicialização do estado da sessão
if 'quiz' not in st.session_state:
    st.session_state.quiz = None
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = [None] * 5
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'show_llm_results' not in st.session_state:
    st.session_state.show_llm_results = False

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Verificação de variáveis de ambiente
    openai_key = os.getenv("OPENAI_API_KEY")
    serper_key = os.getenv("SERPERDEV_API_KEY")
    
    if not openai_key:
        st.error("❌ OPENAI_API_KEY não configurada")
        st.info("Configure a variável de ambiente OPENAI_API_KEY para usar o GPT-4o-mini")
    else:
        st.success("✅ OPENAI_API_KEY configurada")
    
    if not serper_key:
        st.warning("⚠️ SERPERDEV_API_KEY não configurada")
        st.info("Configure a variável de ambiente SERPERDEV_API_KEY para usar o modo Web RAG")
    else:
        st.success("✅ SERPERDEV_API_KEY configurada")

# Aba principal - Gerar questionário e jogar
st.header("📝 Gerar Questionário e Jogar")

# Input da URL
col1, col2 = st.columns([3, 1])
with col1:
    url = st.text_input(
        "URL da qual gerar um questionário:",
        value=URL_EXAMPLES[0],
        placeholder="Digite uma URL..."
    )

with col2:
    st.write("")  # Espaçamento
    generate_btn = st.button("🎯 Gerar Questionário", type="primary")

# Geração do quiz
if generate_btn and url:
    with st.spinner("🔄 Gerando questionário..."):
        try:
            quiz = generate_quiz(url)
            st.session_state.quiz = quiz
            st.session_state.quiz_generated = True
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = [None] * 5
            st.session_state.show_llm_results = False
            st.success("✅ Questionário gerado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao gerar questionário: {str(e)}")
            st.info("Verifique se a URL é válida e se as variáveis de ambiente estão configuradas.")

# Exibição do quiz
if st.session_state.quiz_generated and st.session_state.quiz:
    quiz = st.session_state.quiz
    
    st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
    st.subheader("📋 Questionário")
    
    # Perguntas do quiz
    for i, question in enumerate(quiz["questions"]):
        st.write(f"**Pergunta {i+1}:** {question['question']}")
        
        if not st.session_state.quiz_submitted:
            answer = st.radio(
                "Escolha sua resposta:",
                options=question["options"],
                key=f"question_{i}",
                index=None
            )
            if answer:
                st.session_state.user_answers[i] = answer
        else:
            # Mostrar respostas após submissão
            user_answer = st.session_state.user_answers[i]
            correct_answer = question["options"][ord(question["right_option"]) - ord('a')]
            
            if user_answer:
                if user_answer[0] == question["right_option"]:
                    st.markdown(f'<p class="result-correct">✅ Sua resposta: {user_answer} - Correto!</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="result-wrong">❌ Sua resposta: {user_answer} - Errado</p>', unsafe_allow_html=True)
                    st.markdown(f'<p>✅ Resposta correta: {correct_answer}</p>', unsafe_allow_html=True)
                    # Adicionando a explicação
                    if "explanation" in question and question["explanation"]:
                        st.info(f"**Explicação:** {question['explanation']}")
            else:
                st.markdown(f'<p class="result-wrong">❌ Não respondida</p>', unsafe_allow_html=True)
                st.markdown(f'<p>✅ Resposta correta: {correct_answer}</p>', unsafe_allow_html=True)
                # Adicionando a explicação também para questões não respondidas
                if "explanation" in question and question["explanation"]:
                    st.info(f"**Explicação:** {question['explanation']}")
        
        st.write("---")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not st.session_state.quiz_submitted:
            if st.button("📤 Enviar Respostas", type="primary"):
                st.session_state.quiz_submitted = True
                
                # Calcular pontuação
                score = 0
                for i, answer in enumerate(st.session_state.user_answers):
                    if answer and answer[0] == quiz["questions"][i]["right_option"]:
                        score += 1
                
                score_percentage = (score / 5) * 100
                st.success(f"🎯 Sua pontuação: {score_percentage:.0f}% ({score}/5)")
                st.rerun()
    
    with col2:
        if st.button("🤖 Deixar a LLM Jogar"):
            st.session_state.show_llm_results = True
            st.rerun()
    
    with col3:
        if st.button("🔄 Novo Quiz"):
            st.session_state.quiz = None
            st.session_state.quiz_generated = False
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = [None] * 5
            st.session_state.show_llm_results = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Seção LLM
if st.session_state.show_llm_results and st.session_state.quiz:
    st.header("🤖 Resultados da LLM")
    
    quiz = st.session_state.quiz
    
    # Modo Exame sem Consulta
    st.subheader("📕 Exame sem Consulta")
    st.write("GPT-4o-mini recebe apenas o tópico e as perguntas. Ele responderá com base em seu conhecimento paramétrico e habilidades de raciocínio.")
    
    if st.button("🎯 Tentar Exame sem Consulta"):
        with st.spinner("🤖 LLM respondendo sem consulta..."):
            try:
                answers = get_closed_book_answers(quiz)
                
                score = 0
                details = ""
                
                for i, answer in enumerate(answers):
                    question = quiz['questions'][i]
                    llm_answer = question['options'][ord(answer) - ord('a')] if answer in 'abcd' else "Resposta inválida"
                    correct_answer = question['options'][ord(question['right_option']) - ord('a')]
                    
                    details += f"**Pergunta**: {question['question']}\n\n"
                    details += f"**Resposta da LLM**: {llm_answer}\n\n"
                    details += f"**Resposta correta**: {correct_answer}\n\n"
                    
                    if answer == question['right_option']:
                        score += 1
                        details += "✅ **Resultado**: Correto\n\n"
                    else:
                        details += "❌ **Resultado**: Errado\n\n"
                    
                    details += "---\n\n"
                
                score_percentage = (score / 5) * 100
                st.success(f"🎯 Pontuação da LLM (Exame sem Consulta): {score_percentage:.0f}% ({score}/5)")
                
                with st.expander("📋 Detalhes das Respostas"):
                    st.markdown(details)
                    
            except Exception as e:
                st.error(f"❌ Erro no exame sem consulta: {str(e)}")
    
    # Modo Web RAG
    st.subheader("🔎🌐 RAG Web")
    st.write("Os 3 principais trechos da pesquisa do Google são incluídos no prompt.")
    
    if st.button("🎯 Tentar RAG Web"):
        if not os.getenv("SERPERDEV_API_KEY"):
            st.error("❌ SERPERDEV_API_KEY não configurada. Configure a variável de ambiente para usar o modo Web RAG.")
        else:
            with st.spinner("🌐 LLM respondendo com RAG Web..."):
                try:
                    answers, snippets = get_web_rag_answers_and_snippets(quiz)
                    
                    score = 0
                    details = ""
                    
                    for i, answer in enumerate(answers):
                        question = quiz['questions'][i]
                        llm_answer = question['options'][ord(answer) - ord('a')] if answer in 'abcd' else "Resposta inválida"
                        correct_answer = question['options'][ord(question['right_option']) - ord('a')]
                        
                        details += f"**Pergunta**: {question['question']}\n\n"
                        details += f"**Resposta da LLM**: {llm_answer}\n\n"
                        details += f"**Resposta correta**: {correct_answer}\n\n"
                        
                        if answer == question['right_option']:
                            score += 1
                            details += "✅ **Resultado**: Correto\n\n"
                        else:
                            details += "❌ **Resultado**: Errado\n\n"
                        
                        details += "**Top 3 trechos da pesquisa Google**:\n\n"
                        for snippet in snippets[i]:
                            details += f"- {snippet}\n"
                        details += "\n---\n\n"
                    
                    score_percentage = (score / 5) * 100
                    st.success(f"🎯 Pontuação da LLM (RAG Web): {score_percentage:.0f}% ({score}/5)")
                    
                    with st.expander("📋 Detalhes das Respostas"):
                        st.markdown(details)
                        
                except Exception as e:
                    st.error(f"❌ Erro no RAG Web: {str(e)}")

# Informações sobre o projeto
with st.expander("ℹ️ Sobre o Quiz"):
    st.markdown("""
    ### 🧑‍🏫 Quiz
    
    Aplicação de teste que gera questionários de múltipla escolha a partir de conteúdo web.
    
    **Funcionalidades:**
    - 📝 Geração automática de questionários a partir de URLs
    - 🎮 Modo de jogo para usuários
    - 🤖 Modo LLM com duas variantes:
        - 📕 **Exame sem Consulta**: LLM responde baseado apenas em conhecimento interno
        - 🔎 **RAG Web**: LLM responde com auxílio de pesquisa no Google
    
    **Tecnologias:**
    - 🏗️ **Haystack**: Framework para aplicações de LLM
    - 🤖 **GPT-4o-mini**: Modelo de linguagem da OpenAI
    - 🌐 **Streamlit**: Interface web interativa
    - 🔍 **SerperDev**: API de pesquisa para RAG Web
    
    **Configuração:**
    - Configure `OPENAI_API_KEY` para usar o GPT-4o-mini
    - Configure `SERPERDEV_API_KEY` para usar o modo RAG Web (opcional)
    """)
