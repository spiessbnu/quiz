from .custom_components import QuizParser
from haystack.components.converters import HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.components.websearch.serper_dev import SerperDevWebSearch

from haystack.utils import Secret
from haystack import Pipeline


quiz_generation_template = """Dado o seguinte texto, crie 5 questionários de múltipla escolha em formato JSON.
Cada pergunta deve ter 4 opções diferentes, e apenas uma delas deve estar correta.
As opções devem ser inequívocas.
Cada opção deve começar com uma letra seguida por um ponto e um espaço (ex: "a. opção").
A pergunta também deve mencionar brevemente o tópico geral do texto para que possa ser compreendida isoladamente.
Cada pergunta não deve dar dicas para responder às outras perguntas.
Inclua perguntas desafiadoras, que exijam raciocínio.
Inicie com perguntas de nível fácil e gradativamente apresente questões mais difíceis.

responda apenas com JSON, sem markdown ou descrições.

exemplo de formato JSON que você deve seguir absolutamente:
{"topic": "uma frase explicando o tópico do texto",
 "questions":
  [
    {
      "question": "texto da pergunta",
      "options": ["a. 1ª opção", "b. 2ª opção", "c. 3ª opção", "d. 4ª opção"],
      "right_option": "c"  # letra da opção correta ("a" para a primeira, "b" para a segunda, etc.)
    }, ...
  ]
}

texto:
{% for doc in documents %}{{ doc.content|truncate(4000) }}{% endfor %}
"""


quiz_generation_pipeline = Pipeline()
quiz_generation_pipeline.add_component("link_content_fetcher", LinkContentFetcher())
quiz_generation_pipeline.add_component("html_converter", HTMLToDocument())
quiz_generation_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=quiz_generation_template)
)
quiz_generation_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        generation_kwargs={"max_tokens": 1000, "temperature": 0.5, "top_p": 1},
    ),
)
quiz_generation_pipeline.add_component("quiz_parser", QuizParser())

quiz_generation_pipeline.connect("link_content_fetcher", "html_converter")
quiz_generation_pipeline.connect("html_converter", "prompt_builder")
quiz_generation_pipeline.connect("prompt_builder", "generator")
quiz_generation_pipeline.connect("generator", "quiz_parser")


closed_book_template = """Responda à seguinte pergunta, especificando uma das opções.
O tópico é: {{ topic }}.

Na resposta, especifique apenas a letra correspondente à opção.
Se você não souber a resposta, apenas forneça seu melhor palpite e não forneça nenhum raciocínio.

Por exemplo, se você acha que a resposta é a primeira opção, escreva apenas "a".
Se você acha que a resposta é a segunda opção, escreva apenas "b", e assim por diante.

pergunta: {{ question["question"] }}
opções: {{ question["options"] }}

opção escolhida (a, b, c, ou d):
"""

closed_book_answer_pipeline = Pipeline()
closed_book_answer_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=closed_book_template)
)
closed_book_answer_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        generation_kwargs={"max_tokens": 5, "temperature": 0, "top_p": 1},
    ),
)
closed_book_answer_pipeline.connect("prompt_builder", "generator")


web_rag_template = """Responda à pergunta sobre "{{topic}}", usando seu conhecimento e os trechos extraídos da web.

Na resposta, especifique apenas a letra correspondente à opção.
Se você não souber a resposta, apenas forneça seu melhor palpite e não forneça nenhum raciocínio.

Por exemplo, se você acha que a resposta é a primeira opção, escreva apenas "a".
Se você acha que a resposta é a segunda opção, escreva apenas "b", e assim por diante.

pergunta: {{ question["question"] }}
opções: {{ question["options"] }}

Trechos:
{% for doc in documents %}
- trecho: "{{doc.content}}"
{% endfor %}

opção escolhida (a, b, c, ou d):
"""
web_rag_pipeline = Pipeline()
# Reativando o pipeline web_rag com as chaves API configuradas
web_rag_pipeline.add_component(
    "websearch", SerperDevWebSearch(top_k=3)
)
web_rag_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=web_rag_template)
)
web_rag_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        generation_kwargs={"max_tokens": 5, "temperature": 0, "top_p": 1},
    ),
)
web_rag_pipeline.connect("websearch.documents", "prompt_builder.documents")
web_rag_pipeline.connect("prompt_builder", "generator")
