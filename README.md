# Consultor Inteligente de Carreiras em TI — Etapa 2

Projeto acadêmico de Inteligência Artificial (Ciência da Computação). O sistema entrevista a pessoa usuária, calcula uma **compatibilidade ponderada** com dez trilhas de TI, explica o resultado, identifica **lacunas de conhecimento** para o nível Júnior e gera um **roadmap de estudos personalizado**.

> **Aviso importante:** os percentuais são *estimativas de compatibilidade produzidas pelo modelo* a partir das respostas. **Não são probabilidades de sucesso profissional** nem substituem pesquisa, experiência prática ou orientação humana.

## Funcionalidades

- Questionário em três etapas (Perfil pessoal → Afinidades técnicas → Resultados), sem perder respostas ao voltar e com botão de reiniciar.
- 10 perguntas de afinidade em escala de 1 a 5 (lógica, matemática, design, dados, infraestrutura, segurança, automação, testes, mobile, negócios), além de nível, experiência, ferramentas, objetivos e preferências de atuação.
- Pontuação ponderada com as **dez trilhas** e ranking das três mais compatíveis (empates são preservados).
- Justificativas transparentes: pontos a favor, pontos de atenção e tabela de contribuição de cada resposta.
- Tratamento de incerteza: empates, resultados próximos, perfis equilibrados/moderados e iniciantes.
- Análise de lacunas (Skill Gap) que separa o que o usuário **declarou** do que o sistema **presume**.
- Roadmap por etapas, certificações opcionais e projeto de portfólio para o GitHub.
- Base de conhecimento externa (`regras_carreiras.json`) validada ao carregar.
- Menu lateral com *perfis de demonstração* (personas) para apresentar o sistema.

## Arquitetura

```
┌────────────┐   ┌────────────────────────┐   ┌─────────────────────────────┐
│  app.py    │──▶│ carreiras/motor.py     │◀──│ carreiras/base_conhecimento │
│ (Streamlit)│   │ cálculo de compat.     │   │ carrega + valida o JSON     │
│            │   ├────────────────────────┤   └──────────────▲──────────────┘
│            │──▶│ carreiras/regras_      │                  │
│            │   │ inferencia.py (sinais) │           regras_carreiras.json
│            │──▶│ carreiras/lacunas.py   │           (pesos, textos, regras)
│            │──▶│ carreiras/roadmap.py   │
└────────────┘   └────────────────────────┘
```

Duas camadas com responsabilidades diferentes:

| Camada | Arquivo | O que faz | Altera a pontuação? |
|---|---|---|---|
| **Cálculo de compatibilidade** | `carreiras/motor.py` | Soma ponderada das respostas, ferramentas, objetivos e preferências | Sim |
| **Regras de inferência** | `carreiras/regras_inferencia.py` + `regras_inferencia` no JSON | Condições do tipo *"dados ≥ 4 **e** lógica ≥ 4"* geram sinais ("perfil híbrido") e carreiras alternativas | Não |

### Por que o Experta foi substituído nesta etapa?

A Etapa 1 usava a biblioteca **Experta** (30 regras `@Rule` que somavam pontos inteiros). Na Etapa 2 o cálculo é uma soma ponderada contínua, para a qual um motor de casamento de padrões não traz vantagem. Além disso, o próprio README da Etapa 1 já alertava que o Experta é antigo e pode falhar em versões recentes do Python (exigia fixar `frozendict`). Por isso:

- o cálculo ficou em Python puro (simples de explicar e de testar, sem dependências extras);
- as regras qualitativas passaram para o JSON, mantendo a ideia de *base de regras separada do motor*;
- a Etapa 1 continua disponível, sem alterações, no repositório original: https://github.com/devmarcus-souza/consultor-inteligente-carreiras-ti.

Esta versão **não** declara ter regras Experta: as regras implementadas agora são as 14 regras de inferência do JSON (`R01`–`R14`), documentadas em `MATRIZ_DE_DECISAO.md`.

## Fórmula de compatibilidade

Para cada carreira *c*:

```
n_i   = (resposta_i − 1) / 4                  normaliza a escala 1..5 para 0..1
w_ci  = peso_ci / Σ_j peso_cj                 pesos da carreira (0..10 no JSON), normalizados para somar 1
A_c   = Σ_i  w_ci · n_i                       afinidade (0..1)
T_c   = 1 − Π_t (1 − r_tc)                    ferramentas conhecidas (0..1), com retornos decrescentes
O_c   = max_o  r_oc                           objetivos escolhidos (0..1)
P_c   = max_p  r_pc                           preferências de atuação (0..1)

S_c   = 100 · ( 0,80·A_c + 0,08·T_c + 0,08·O_c + 0,04·P_c )
```

- `r_tc`, `r_oc`, `r_pc` são relevâncias de 0 a 1 definidas no JSON (por exemplo, Docker tem relevância 1,0 para DevOps).
- Os quatro coeficientes (0,80 / 0,08 / 0,08 / 0,04) ficam em `parametros` e **precisam somar 1**.
- Fatores complementares valem no máximo 20 dos 100 pontos, então ferramentas e objetivos **não dominam** o resultado.
- Nenhuma dimensão pode ter mais de 35% do peso de uma carreira (validado ao carregar), então **uma única resposta não decide todas as trilhas**.

**Exemplo (persona analítica, Ciência de Dados):** afinidade = 61,6 pontos; ferramentas (Python, Pandas/NumPy, Estatística, SQL) = 8,0; objetivo "gerar insights" = 8,0; preferência "experimentos" = 4,0. Total = **81,6%**. A tabela completa de contribuições aparece na interface, no expander *"Como a pontuação desta trilha foi calculada"*.

### Respostas ausentes, inválidas e empates

- Resposta ausente ou inválida (fora de 1–5, texto, booleano etc.) é tratada como **neutra (3)**, com aviso. Se houver menos de 5 respostas válidas, o sistema não gera recomendação.
- **Empate** = mesma pontuação no nível de precisão exibido (1 casa decimal). Empatadas dividem a posição (1º, 2º, 2º, 4º) e, se houver empate na 3ª posição, **todas** entram no resultado.
- Classificação do resultado: *clara* (1º lidera por ≥ 8 pontos), *moderada* (3 a 8), *ambígua* (< 3) e *empate*. Os limites ficam em `parametros`.
- Perfil com todas as respostas iguais (por exemplo, tudo 3) e sem ferramentas/objetivos gera empate entre as dez trilhas, e o sistema avisa que não há diferenciação.

## Estrutura dos arquivos

```
consultor-inteligente-carreiras-ti/
├── app.py                      interface Streamlit (3 etapas)
├── regras_carreiras.json       base de conhecimento (pesos, textos, regras)
├── requirements.txt            dependências da Etapa 2 (somente Streamlit)
├── MATRIZ_DE_DECISAO.md        tabelas de pesos e regras
├── README.md
├── .gitignore                  impede o envio de .venv e caches
├── carreiras/
│   ├── base_conhecimento.py    carrega e valida o JSON
│   ├── motor.py                cálculo de compatibilidade e ranking
│   ├── regras_inferencia.py    regras qualitativas do JSON
│   ├── lacunas.py              análise de lacunas
│   ├── roadmap.py              geração do roadmap
│   └── personas.py             perfis de teste e demonstração
└── tests/                      testes automatizados (unittest)
```

## Instalação no Windows

Requer Python 3.10 ou superior (testado com 3.12; deve funcionar com 3.13). No PowerShell, dentro da pasta do projeto:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente de novo.

## Executando o aplicativo

```powershell
streamlit run app.py
```

Abra no navegador o endereço exibido no terminal (normalmente `http://localhost:8501`).

## Executando os testes

Os testes usam apenas a biblioteca padrão (`unittest`), sem instalar nada:

```powershell
python -m unittest discover -v
```

Cobertura principal: base JSON (carregamento, dez carreiras, pesos, validações de erro), motor (limites 0–100, ordenação, empates, respostas ausentes/inválidas, extremos), lacunas, roadmap das dez trilhas, personas e um teste de fumaça da interface (com Streamlit simulado). Os testes são classes `unittest`, que o `pytest` também costuma conseguir executar (não verificado neste pacote).

## Personas utilizadas

Resultados obtidos com os pesos atuais do JSON (podem mudar se você ajustar os pesos):

| Persona | Perfil | Resultado (top 3) | Leitura |
|---|---|---|---|
| Analítica | Matemática e dados altos, Python/Pandas | Ciência de Dados 81,6 · Eng. de Dados 61,5 · Back-end 53,6 | Resultado claro |
| Visual | Design alto, HTML/CSS/JS/Figma | Front-end 69,1 · Mobile 54,8 · Produto 52,9 | Resultado claro |
| Infra/Segurança | Redes, Linux, segurança | Cibersegurança 74,0 · Cloud 66,4 · DevOps 65,7 | Moderado: Cloud e DevOps são alternativas próximas |
| Negócios/Produto | Negócios alto, pouca programação | Produto 65,6 · Front-end 46,7 · QA 38,3 | Resultado claro |
| Ambígua (dados + programação) | Dados, lógica e automação altos | Ciência de Dados 67,7 · Eng. de Dados 66,6 · Back-end 61,5 | **Ambíguo**: diferença de ~1 ponto, o sistema não força um vencedor |
| Iniciante | Sem ferramentas, respostas moderadas | Produto 48,8 · Front-end 48,6 · Mobile 45,4 | **Ambíguo**: regra R10 recomenda experimentar projetos curtos |
| Design + mobile | Design e mobile altos | Mobile 74,3 · Front-end 68,6 · Produto 48,5 | Trilhas vizinhas (regra R02) |
| Equilibrada | Tudo 3, sem ferramentas | Empate entre as dez trilhas (40,0) | Sem diferenciação |

No aplicativo, use o menu lateral **Perfis de demonstração → Carregar perfil**.

## Limitações do modelo

- Os pesos e as relevâncias são **julgamentos iniciais** do autor, baseados em descrições gerais das carreiras. Não foram calibrados com dados reais de pessoas ou vagas.
- Cada dimensão tem uma única pergunta; um questionário real usaria várias perguntas por dimensão e seria validado.
- A análise de lacunas só conhece o que foi declarado: ela **presume** lacunas quando não há ferramenta declarada e não consegue verificar conhecimentos sem ferramenta associada (por exemplo, "casos de teste" ou "discovery").
- Percentuais indicam compatibilidade *relativa* às regras do modelo, não aptidão, desempenho ou chance de contratação.
- Certificações são apenas sugestões opcionais; disponibilidade, requisitos e custos mudam e devem ser conferidos no site do emissor. O sistema não informa preços nem prazos oficiais.
- O mercado e as tecnologias mudam; revise o JSON periodicamente.
- Testes automatizados verificam a lógica, não a qualidade pedagógica dos conteúdos.

## Como atualizar pesos e a base de conhecimento

Tudo fica em `regras_carreiras.json`; **não é preciso mexer no `app.py`**.

- **Ajustar pesos:** em `carreiras.<id>.pesos`, altere os valores (0 a 10) de cada dimensão. Eles são normalizados automaticamente. Nenhuma dimensão pode passar de 35% do total.
- **Mudar o peso dos fatores:** em `parametros` (`peso_afinidade`, `peso_ferramentas`, `peso_objetivos`, `peso_preferencias`; devem somar 1).
- **Nova carreira:** copie o bloco de uma carreira existente dentro de `carreiras`, dê um novo id e preencha todos os campos (nome, descrição, características, pesos, competências, roadmap, certificações, projeto). Se quiser que ferramentas, objetivos e preferências a reconheçam, inclua o id em `relevancia`.
- **Nova ferramenta, objetivo ou preferência:** adicione um item à lista correspondente com `id`, `nome` e `relevancia`.
- **Nova regra de inferência:** adicione um item em `regras_inferencia` com `condicoes` (campo, operador, valor), `carreiras` e `mensagem`.
- **Validação:** ao abrir o app (ou rodar os testes), o arquivo é verificado. Erros como JSON inválido, peso fora de 0–10, dimensão faltando ou campo obrigatório vazio aparecem com uma mensagem indicando o local.

## Publicando em um novo repositório

Esta Etapa 2 vive em um repositório separado; a Etapa 1 (https://github.com/devmarcus-souza/consultor-inteligente-carreiras-ti) permanece intacta.

1. No GitHub, clique em **New repository**, escolha um nome (por exemplo `consultor-carreiras-ti-etapa2`) e **não** marque "Add a README" nem `.gitignore` (o projeto já tem os dois).
2. Extraia o ZIP e abra o PowerShell dentro da pasta do projeto.
3. Teste antes de publicar (veja "Instalação no Windows"):
   ```powershell
   python -m unittest discover -v
   streamlit run app.py
   ```
4. Inicie o Git e faça o primeiro commit:
   ```powershell
   git init
   git branch -M main
   git add .
   git status
   git commit -m "feat: Consultor de Carreiras em TI - Etapa 2 (pontuação ponderada, base JSON, lacunas, roadmap e testes)"
   ```
   Antes do commit, confira no `git status` que a pasta `.venv` **não** aparece.
5. Conecte ao repositório criado (troque `SEU-USUARIO` e o nome) e envie:
   ```powershell
   git remote add origin https://github.com/SEU-USUARIO/consultor-carreiras-ti-etapa2.git
   git push -u origin main
   ```
