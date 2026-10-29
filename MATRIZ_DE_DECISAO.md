# Matriz de decisão

> As tabelas da Etapa 2 foram **geradas a partir de `regras_carreiras.json`**. Para alterar pesos, edite o JSON (não este arquivo) e atualize estas tabelas manualmente.

## 1. Pesos das dimensões por trilha (Etapa 2)

Cada linha mostra quanto cada dimensão de afinidade (resposta de 1 a 5) pesa no cálculo da trilha, em %. Cada linha soma 100%.

| Trilha | Lógica | Mat./Est. | Design/UX | Dados | Infra/Redes | Segurança | Automação | Testes/QA | Mobile | Negócios |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Desenvolvimento Back-end | 24 | 8 | 0 | 16 | 8 | 11 | 11 | 13 | 3 | 8 |
| Desenvolvimento Front-end e UI/UX | 17 | 3 | 29 | 6 | 0 | 6 | 6 | 11 | 9 | 14 |
| Ciência de Dados e Machine Learning | 16 | 26 | 3 | 26 | 3 | 3 | 8 | 5 | 0 | 11 |
| Engenharia de Dados | 17 | 7 | 0 | 24 | 14 | 7 | 17 | 10 | 0 | 5 |
| Cibersegurança | 12 | 8 | 0 | 8 | 20 | 25 | 12 | 8 | 2 | 5 |
| DevOps e SRE | 13 | 3 | 0 | 5 | 23 | 13 | 26 | 13 | 0 | 5 |
| Computação em Nuvem e Cloud Architecture | 11 | 3 | 0 | 8 | 27 | 16 | 19 | 5 | 0 | 11 |
| Desenvolvimento Mobile | 17 | 2 | 17 | 5 | 2 | 7 | 5 | 10 | 24 | 10 |
| Engenharia de Qualidade e Testes (QA) | 12 | 2 | 5 | 8 | 5 | 8 | 15 | 25 | 8 | 12 |
| Gestão de Produtos (Product Management) | 9 | 9 | 15 | 18 | 0 | 3 | 6 | 6 | 6 | 29 |

## 2. Fatores do cálculo

| Fator | Peso na pontuação final | Como entra |
|---|---:|---|
| Afinidades (10 perguntas, escala 1–5) | 80% | Soma ponderada das respostas normalizadas |
| Ferramentas conhecidas | 8% | Cada ferramenta tem relevância 0–1 por trilha; combinadas com retornos decrescentes |
| Objetivos profissionais | 8% | Vale a maior relevância entre os objetivos escolhidos |
| Preferências de atuação | 4% | Vale a maior relevância entre as preferências escolhidas |

Os fatores complementares somam no máximo 20 pontos de 100, portanto não dominam o resultado.

## 3. Ferramentas e trilhas de maior relevância

| Ferramenta | Trilhas (relevância) |
|---|---|
| Python | Ciência de Dados e Machine Learning (0.8), Engenharia de Dados (0.7), Desenvolvimento Back-end (0.6) |
| Java ou C# | Desenvolvimento Back-end (0.8), Desenvolvimento Mobile (0.3), Engenharia de Qualidade e Testes (0.2) |
| JavaScript ou TypeScript | Desenvolvimento Front-end e UI/UX (0.8), Desenvolvimento Mobile (0.4), Desenvolvimento Back-end (0.3) |
| HTML e CSS | Desenvolvimento Front-end e UI/UX (1.0), Engenharia de Qualidade e Testes (0.2) |
| Figma ou outra ferramenta de prototipação | Desenvolvimento Front-end e UI/UX (0.7), Gestão de Produtos (0.5), Desenvolvimento Mobile (0.4) |
| SQL e bancos de dados | Engenharia de Dados (1.0), Desenvolvimento Back-end (0.6), Ciência de Dados e Machine Learning (0.5) |
| Git e GitHub | DevOps e SRE (0.5), Desenvolvimento Back-end (0.3), Desenvolvimento Front-end e UI/UX (0.3) |
| Linux e linha de comando | DevOps e SRE (0.8), Cibersegurança (0.8), Computação em Nuvem e Cloud Architecture (0.7) |
| Redes de computadores (TCP/IP, DNS, HTTP) | Cibersegurança (0.8), Computação em Nuvem e Cloud Architecture (0.8), DevOps e SRE (0.5) |
| APIs REST (consumo ou criação) | Desenvolvimento Back-end (0.8), Desenvolvimento Mobile (0.5), Engenharia de Qualidade e Testes (0.5) |
| Docker e contêineres | DevOps e SRE (1.0), Computação em Nuvem e Cloud Architecture (0.5), Desenvolvimento Back-end (0.4) |
| CI/CD (GitHub Actions, GitLab CI, Jenkins...) | DevOps e SRE (1.0), Engenharia de Qualidade e Testes (0.5), Desenvolvimento Back-end (0.3) |
| AWS, Azure ou Google Cloud | Computação em Nuvem e Cloud Architecture (1.0), DevOps e SRE (0.6), Engenharia de Dados (0.4) |
| Infraestrutura como código (Terraform, CloudFormation...) | DevOps e SRE (0.9), Computação em Nuvem e Cloud Architecture (0.8), Cibersegurança (0.2) |
| Flutter, React Native, Kotlin ou Swift | Desenvolvimento Mobile (1.0), Desenvolvimento Front-end e UI/UX (0.3) |
| Ferramentas de testes automatizados (pytest, Selenium, Cypress...) | Engenharia de Qualidade e Testes (1.0), DevOps e SRE (0.3), Desenvolvimento Back-end (0.3) |
| Pandas e NumPy | Ciência de Dados e Machine Learning (1.0), Engenharia de Dados (0.4) |
| scikit-learn, TensorFlow ou PyTorch | Ciência de Dados e Machine Learning (1.0) |
| Estatística aplicada | Ciência de Dados e Machine Learning (0.9), Gestão de Produtos (0.2) |
| ETL/ELT (Airflow, dbt, Spark...) | Engenharia de Dados (1.0), Ciência de Dados e Machine Learning (0.3) |
| Ferramentas de segurança (Nmap, Wireshark, Burp Suite...) | Cibersegurança (1.0), DevOps e SRE (0.2), Engenharia de Qualidade e Testes (0.2) |
| Ferramentas ágeis (Jira, Trello, Scrum/Kanban) | Gestão de Produtos (0.8), Engenharia de Qualidade e Testes (0.4), DevOps e SRE (0.1) |
| Monitoramento (Prometheus, Grafana ou similares) | DevOps e SRE (0.9), Computação em Nuvem e Cloud Architecture (0.5), Cibersegurança (0.3) |
| Excel, Power BI ou ferramentas de BI | Gestão de Produtos (0.5), Ciência de Dados e Machine Learning (0.4), Engenharia de Dados (0.3) |

## 4. Regras de inferência (qualitativas)

Não alteram a pontuação; geram sinais e alternativas.

| Id | Nome | Condições | Trilhas sugeridas |
|---|---|---|---|
| R01 | Dados + programação | dados >= 4 e logica >= 4 | data_science, data_engineering, backend |
| R02 | Design + mobile | design >= 4 e mobile >= 4 | mobile, frontend |
| R03 | Infraestrutura + segurança | infra >= 4 e seguranca >= 4 | security, cloud, devops |
| R04 | Infraestrutura + automação | infra >= 4 e automacao >= 4 | devops, cloud |
| R05 | Testes + automação | testes >= 4 e automacao >= 4 | qa, devops |
| R06 | Negócios + design | negocios >= 4 e design >= 4 | product, frontend |
| R07 | Negócios + dados | negocios >= 4 e dados >= 4 | product, data_science |
| R08 | Matemática + dados | matematica >= 4 e dados >= 4 | data_science |
| R09 | Pouca programação + negócios | logica <= 2 e negocios >= 4 | product, qa |
| R10 | Iniciante sem ferramentas | nivel == 0 e num_ferramentas == 0 | — |
| R11 | Segurança + programação | seguranca >= 4 e logica >= 4 | security, backend |
| R12 | Automação + programação | automacao >= 4 e logica >= 4 | devops, data_engineering, backend |
| R13 | Respostas moderadas | media_respostas >= 2.5 e media_respostas <= 3.5 e amplitude_respostas <= 2 | — |
| R14 | Interesses equilibrados e altos | media_respostas >= 3.8 e amplitude_respostas <= 2 | — |

## 5. Matriz da Etapa 1 (histórico)

Mantida para registro. Na Etapa 1 havia três regras principais por trilha (30 regras Experta), além de um ajuste de pontuação para afinidade matemática. Esse código está no repositório da Etapa 1.

| Trilha | Atividade-chave | Ferramenta | Valor esperado |
|---|---|---|---|
| Back-end | Algoritmos e regras de negócio | Python | Serviços que processam informações |
| Front-end & UI/UX | Interfaces e experiência visual | JavaScript | Interface agradável e fácil |
| Ciência de Dados/ML | Padrões e previsões | Python + matemática alta | Descobertas baseadas em dados |
| Engenharia de Dados | Organização de dados e pipelines | SQL/bancos de dados | Dados disponíveis para equipes |
| Cibersegurança | Investigar vulnerabilidades | Linux/redes | Proteção contra ataques |
| DevOps & SRE | Automatizar e monitorar | Docker/Git/CI/CD | Disponibilidade e implantações confiáveis |
| Cloud | Planejar infraestrutura em nuvem | AWS/Azure/GCP | Infraestrutura escalável |
| Mobile | Aplicativos para dispositivos móveis | Flutter/React Native | Aplicativos para celulares/tablets |
| QA | Testar e validar software | Testes automatizados | Software estável e com menos defeitos |
| Gestão de Produtos | Planejar e priorizar funcionalidades | Ferramentas ágeis | Valor para usuários e negócio |
