# Divisão de registros em Teste e Controle por dia

Este documento explica o funcionamento do script `main.py`, suas regras e como executá-lo.

## 1. Objetivo

O script lê uma tabela de um arquivo CSV ou Excel e sorteia metade das linhas de cada dia para o grupo **Teste**. As outras linhas ficam no grupo **Controle**.

O arquivo de saída contém todas as linhas da entrada, na mesma ordem, com a coluna adicional `Grupo`.

Quando a quantidade de linhas de um dia é ímpar, o grupo Teste recebe uma linha a mais que o Controle.

| Linhas no dia | Teste | Controle |
| ---: | ---: | ---: |
| 1 | 1 | 0 |
| 2 | 1 | 1 |
| 3 | 2 | 1 |
| 4 | 2 | 2 |
| 5 | 3 | 2 |
| 6 | 3 | 3 |
| 7 | 4 | 3 |
| 10 | 5 | 5 |

**A unidade de sorteio é a linha, não o CPF único.** Se o mesmo CPF aparece em várias linhas, cada linha participa separadamente e pode receber um grupo diferente. O script não remove duplicatas.

## 2. Instalação e execução

### Dependências

Use Python com pandas, NumPy e openpyxl instalados:

```bash
pip install -r requirements.txt
```

O tratamento de datas usa `format="mixed"`, disponível no pandas 2.0 ou posterior. O openpyxl permite ler e escrever arquivos `.xlsx`.

### Execução básica

Na pasta que contém `main.py` e o arquivo de entrada:

```bash
python main.py dados.xlsx
```

O script gera uma semente aleatória, imprime seu valor e grava um CSV com um nome como:

```text
selecionados-123.csv
```

O número no nome corresponde à semente usada. Apesar do nome `selecionados`, esse arquivo contém tanto Teste quanto Controle.

### Gerar Excel

```bash
python main.py dados.xlsx --saida grupos.xlsx
```

### Usar CSV como entrada

```bash
python main.py dados.csv --saida grupos.csv
```

### Repetir o sorteio com uma semente fixa

```bash
python main.py dados.xlsx --saida grupos.xlsx --seed 123
```

### Agrupar por outra coluna de data

```bash
python main.py dados.xlsx --coluna-data "Última Doação" --saida grupos.xlsx
```

Use aspas quando o nome de uma coluna ou o caminho de um arquivo contiver espaços.

## 3. Bibliotecas utilizadas

```python
import argparse
from pathlib import Path

import pandas as pd
import numpy as np
```

- **argparse:** interpreta os argumentos informados no terminal.
- **Path:** representa os caminhos dos arquivos e permite consultar suas extensões e seus caminhos absolutos.
- **pandas:** lê a tabela, interpreta datas, agrupa linhas por dia, sorteia registros e exporta o resultado.
- **NumPy:** gera a semente aleatória e cria o vetor de classificação dos registros.

## 4. Início do programa

No final do arquivo existe:

```python
if __name__ == "__main__":
    main()
```

Isso chama `main()` quando o arquivo é executado diretamente, por exemplo, com `python main.py dados.xlsx`.

Se outro código importar a função `selecionar_metade_por_dia`, o processamento de arquivos não será executado automaticamente.

## 5. Leitura dos argumentos do terminal

A função `main()` cria o interpretador de argumentos e executa:

```python
args = parser.parse_args()
```

Essa etapa acontece antes de acessar `args.seed`, `args.entrada` ou outros argumentos.

| Argumento | Obrigatório? | Padrão | Função |
| --- | --- | --- | --- |
| `entrada` | Sim | — | Caminho do arquivo de entrada |
| `--saida` | Não | `selecionados-<seed>.csv` | Caminho do arquivo gerado |
| `--coluna-data` | Não | `Data de envio da notificação` | Coluna usada para definir os dias |
| `--seed` | Não | Inteiro aleatório | Semente usada no sorteio |

O argumento `--seed` deve ser um inteiro entre `0` e `4294967295`, intervalo aceito pelo mecanismo de sorteio usado. O código não faz uma validação própria desse intervalo; valores fora dele podem causar erro no pandas/NumPy.

## 6. Definição da semente

O script primeiro verifica se uma semente foi informada:

```python
seed = args.seed
if seed is None:
    seed = int(np.random.default_rng().integers(0, 2**32))
```

Se não houver `--seed`, o NumPy gera um inteiro aleatório entre `0` e `2**32 - 1`. A conversão `int()` transforma o valor em um inteiro Python.

O programa mostra o valor escolhido:

```text
Semente do sorteio: 123
```

A semente controla a sequência pseudoaleatória utilizada no sorteio. Para a mesma entrada, com a mesma ordem das linhas, a mesma coluna de agrupamento e o mesmo ambiente de bibliotecas, uma semente fixa permite reproduzir a classificação.

Uma nova execução sem `--seed` normalmente gera outra semente, mas isso não garante uma classificação diferente: sorteios distintos podem coincidir, especialmente em grupos pequenos.

## 7. Definição do arquivo de saída

Depois de conhecer a semente, o script define o nome padrão quando `--saida` não foi informado:

```python
if args.saida is None:
    args.saida = Path(f"selecionados-{seed}.csv")
```

O nome padrão depende da semente. Se você informar `--saida grupos.xlsx`, esse caminho será usado.

Os caminhos relativos são interpretados a partir da pasta onde o comando foi executado. Se o arquivo de saída já existir, a exportação o sobrescreve.

## 8. Leitura dos dados

### Entrada Excel

Quando a extensão é `.xlsx`, o script usa:

```python
df = pd.read_excel(args.entrada, dtype=str)
```

A primeira planilha do arquivo é lida, usando a primeira linha como cabeçalho. Os valores das colunas são carregados como texto, com valores ausentes tratados pelo pandas.

### Entrada CSV

Para as outras extensões, o script tenta ler como CSV:

```python
df = pd.read_csv(args.entrada, sep=None, engine="python", dtype=str)
```

- `sep=None`: solicita a detecção automática do separador.
- `engine="python"`: usa o mecanismo que permite essa detecção.
- `dtype=str`: lê os valores como texto, importante para não descartar zeros à esquerda do CPF.

O script usa a codificação padrão de leitura do pandas. CSVs em outras codificações podem exigir um ajuste no parâmetro `encoding`.

O programa trabalha com os valores da tabela. Ele não copia a formatação visual, fórmulas, gráficos ou outras planilhas do arquivo Excel original.

## 9. Limpeza dos nomes das colunas

```python
df.columns = df.columns.str.strip()
```

Remove espaços no começo e no final dos cabeçalhos. Por exemplo, `" CPF "` passa a ser `"CPF"`.

Não altera letras maiúsculas, acentos ou espaços internos. Portanto, `CPF` e `cpf` continuam sendo nomes diferentes.

## 10. Chamada da função de classificação

```python
resultado = selecionar_metade_por_dia(df, args.coluna_data, seed)
```

A função recebe:

1. `df`: tabela carregada em um DataFrame.
2. `coluna_data`: nome da coluna usada para agrupar por dia.
3. `seed`: semente do sorteio.

Apesar de seu nome, a função retorna **todas as linhas classificadas**, e não apenas as sorteadas.

As próximas etapas acontecem dentro dessa função.

## 11. Verificação da coluna de data

```python
if coluna_data not in df.columns:
    raise ValueError(f"Coluna não encontrada: {coluna_data}")
```

Se a coluna solicitada não existir, o processamento para com uma mensagem que indica o nome esperado.

## 12. Preparação das datas

```python
valores = df[coluna_data].astype("string").str.strip()
```

Cria uma série de texto para interpretar as datas e remove espaços nas extremidades. Isso não substitui a coluna original de datas na saída.

Em seguida, identifica valores que começam com o padrão ano-mês-dia:

```python
formato_iso = valores.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
```

O padrão significa:

- `^`: começo do texto.
- `\d{4}`: quatro dígitos para o ano.
- `-`: hífen.
- `\d{2}`: dois dígitos para mês e dia.
- `na=False`: valores ausentes não são classificados como ISO.

Exemplos identificados como ISO:

```text
2026-11-14
2026-11-14 00:00:00
```

Essa identificação decide como interpretar cada valor. A validação de que ele representa uma data válida ocorre na conversão seguinte.

## 13. Conversão das datas

Primeiro, a função cria uma série inicialmente preenchida com `NaT`, que representa data ausente:

```python
datas = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
```

### Valores ISO

```python
datas.loc[formato_iso] = pd.to_datetime(
    valores.loc[formato_iso], format="ISO8601", errors="raise"
)
```

Esses valores são interpretados como **ano-mês-dia**. Assim, `2026-11-03` representa **3 de novembro de 2026**.

### Outros valores

```python
datas.loc[~formato_iso] = pd.to_datetime(
    valores.loc[~formato_iso], format="mixed", dayfirst=True, errors="raise"
)
```

- `~formato_iso`: seleciona os valores que não foram identificados como ISO.
- `format="mixed"`: permite inferir o formato individualmente para cada valor.
- `dayfirst=True`: orienta a interpretação de datas ambíguas com o dia primeiro, como `03/11/2026`.
- `errors="raise"`: faz o processamento parar se algum valor não puder ser convertido.

Separar os valores ISO dos brasileiros evita a troca de dia e mês que pode acontecer ao aplicar `dayfirst=True` a datas vindas do Excel.

Este fluxo foi feito para datas brasileiras e datas ISO comuns, sem fuso horário. Valores numéricos de data serial do Excel ou formatos diferentes podem exigir tratamento adicional.

## 14. Verificação de datas ausentes

```python
if datas.isna().any():
    raise ValueError(f"Existem datas vazias na coluna {coluna_data}.")
```

Se houver valores ausentes após a conversão, a função interrompe o processamento. Uma string vazia também pode causar erro já na etapa de conversão, dependendo de como foi carregada.

As linhas com datas inválidas ou ausentes não são descartadas silenciosamente.

## 15. Semente quando a função é usada diretamente

A função também permite que outro programa a chame sem informar a semente:

```python
if seed is None:
    seed = int(np.random.default_rng().integers(0, 2**32))
```

Quando o script é executado pelo terminal, `main()` já gerou ou recebeu a semente e a passa para a função. Nesse caso, não é gerada uma segunda semente.

## 16. Agrupamento pelo dia

```python
grupos = df.reset_index(drop=True).groupby(
    datas.reset_index(drop=True).dt.normalize(), sort=True
)
```

### Índices posicionais

`reset_index(drop=True)` cria índices únicos de `0` até `N - 1` para o sorteio. Isso permite distinguir linhas mesmo se o DataFrame original tiver índices repetidos.

Essa redefinição é usada na estrutura de trabalho. O resultado é construído a partir de uma cópia da tabela original.

### Remoção do horário para agrupamento

`dt.normalize()` transforma o horário das datas em meia-noite, mantendo o dia:

```text
2026-11-03 08:00:00 → 2026-11-03 00:00:00
2026-11-03 15:30:00 → 2026-11-03 00:00:00
```

As duas linhas passam a pertencer ao mesmo grupo diário.

### Critério de agrupamento

Por padrão, todas as linhas com a mesma `Data de envio da notificação` pertencem ao mesmo grupo, independentemente de instituição, sexo ou CPF.

Não há uma cota separada por instituição ou sexo. Por exemplo, se um dia tem 10 linhas de uma instituição e 20 de outra, o sorteio considera um conjunto de 30 linhas e escolhe 15 para Teste.

`sort=True` percorre os grupos em ordem de data. Isso não muda a ordem final das linhas exportadas.

## 17. Classificação inicial como Controle

```python
classificacao = np.full(len(df), "Controle", dtype=object)
```

Cria um vetor com uma posição para cada linha, inicialmente preenchido com `Controle`.

Depois, apenas as posições sorteadas serão alteradas para `Teste`. Assim, nenhuma linha fica sem classificação.

## 18. Quantidade sorteada por dia

Para cada grupo diário, a quantidade de linhas de Teste é calculada por:

```python
(len(grupo) + 1) // 2
```

`//` representa divisão inteira.

Para um grupo com 5 linhas:

```text
(5 + 1) // 2 = 3
```

Para um grupo com 6 linhas:

```text
(6 + 1) // 2 = 3
```

A expressão equivale à metade da quantidade arredondada para cima. Não se adiciona uma linha ao arquivo: apenas se atribui uma linha a mais ao Teste quando o total diário é ímpar.

## 19. Sorteio e atribuição do grupo Teste

```python
for _, grupo in grupos:
    selecionados = grupo.sample(n=(len(grupo) + 1) // 2, random_state=seed)
    classificacao[selecionados.index.to_numpy()] = "Teste"
```

- `grupo.sample(...)`: sorteia a quantidade calculada de linhas.
- O sorteio é sem reposição, comportamento padrão de `sample`: a mesma posição não é sorteada duas vezes no mesmo grupo.
- Não são informados pesos, portanto as linhas do grupo diário têm a mesma chance de seleção.
- `random_state=seed`: controla a sequência pseudoaleatória.
- `selecionados.index.to_numpy()`: obtém as posições sorteadas.
- Essas posições recebem `Teste` no vetor de classificação.

A implementação usa a mesma semente em cada chamada de `sample`. Por isso, grupos com a mesma quantidade de linhas podem ter o mesmo padrão de posições relativas sorteadas. Não é usado um gerador único avançando continuamente entre os dias.

## 20. Criação da tabela de resultado

```python
resultado = df.copy()
```

Cria uma cópia com todas as linhas e colunas da entrada. O sorteio não filtra a tabela nem reorganiza suas linhas.

Em seguida, a função trata o CPF e adiciona a classificação.

## 21. Tratamento da coluna CPF

O tratamento acontece quando existe uma coluna chamada exatamente `CPF`:

```python
if "CPF" in resultado.columns:
    cpf = resultado["CPF"].astype("string").str.strip()
    numericos = cpf.str.fullmatch(r"[0-9]{1,11}", na=False)
    cpf.loc[numericos] = cpf.loc[numericos].str.zfill(11)
    resultado["CPF"] = cpf
```

### Conversão para texto

`astype("string")` mantém o CPF como texto e preserva valores ausentes. `str.strip()` remove espaços nas extremidades.

### Identificação de valores numéricos

`str.fullmatch(r"[0-9]{1,11}", na=False)` identifica valores compostos somente por 1 a 11 dígitos.

### Preenchimento com zeros

`str.zfill(11)` adiciona zeros à esquerda até completar 11 caracteres.

| Valor de entrada | Valor no resultado |
| --- | --- |
| `00123456789` | `00123456789` |
| `123456789` | `00123456789` |
| `01234567890` | `01234567890` |
| `12343678901` | `12343678901` |
| `123.456.789-01` | `123.456.789-01` |
| Ausente | Ausente |

CPFs com pontuação não recebem zeros e mantêm sua pontuação. O script não verifica os dígitos verificadores do CPF. Valores com mais de 11 dígitos ou caracteres como `.0` não são corrigidos por essa regra.

Quando um CPF numérico perdeu zeros no Excel, o preenchimento assume que o identificador deve ter 11 dígitos. Ele não consegue recuperar outros tipos de alteração no valor original.

## 22. Inclusão da coluna Grupo

```python
resultado["Grupo"] = classificacao
return resultado
```

Adiciona `Grupo` com `Teste` ou `Controle` para cada linha e devolve a tabela completa.

Se a entrada já possuir uma coluna chamada `Grupo`, seus valores serão substituídos pela nova classificação.

Exemplo ilustrativo de saída para um dia com 5 linhas:

| Última Doação | Última Instituição Coletora | CPF | Sexo | Data de envio da notificação | Grupo |
| --- | --- | --- | --- | --- | --- |
| 03/09/2026 | B3013 | 00123456789 | Masculino | 03/11/2026 | Teste |
| 03/09/2026 | B3013 | 01234567890 | Feminino | 03/11/2026 | Controle |
| 03/09/2026 | B3208 | 12343678901 | Masculino | 03/11/2026 | Teste |
| 03/09/2026 | B3209 | 00012345678 | Feminino | 03/11/2026 | Controle |
| 03/09/2026 | B3483 | 09876543210 | Masculino | 03/11/2026 | Teste |

O exemplo demonstra a proporção de 3 Teste e 2 Controle. As linhas efetivamente sorteadas dependem da semente e da entrada.

## 23. Exportação do resultado

### Excel

Se a saída terminar em `.xlsx`:

```python
resultado.to_excel(args.saida, index=False)
```

Todas as linhas e colunas do resultado são gravadas em uma planilha. `index=False` evita adicionar uma coluna com o índice interno do pandas.

Como o CPF foi convertido para texto, ele é salvo no Excel como texto, preservando os zeros à esquerda.

### CSV

Para outras extensões de saída:

```python
resultado.to_csv(args.saida, sep=";", index=False, encoding="utf-8-sig")
```

- `sep=";"`: separa as colunas por ponto e vírgula.
- `index=False`: não exporta o índice interno.
- `encoding="utf-8-sig"`: usa UTF-8 com uma marca de codificação que ajuda o Excel a reconhecer os acentos.

Um CSV não armazena o tipo das colunas. Os zeros ficam presentes no conteúdo do arquivo, mas o Excel pode removê-los ao interpretar CPF como número. Ao importar o CSV no Excel, defina a coluna CPF como **Texto**, ou gere diretamente uma saída `.xlsx`.

## 24. Resumo mostrado no terminal

Depois de gravar o arquivo, o programa imprime:

```text
Total: 11 linhas.
Teste: 6 linhas.
Controle: 5 linhas.
Arquivo salvo em: C:\caminho\grupos.xlsx
```

As contagens são obtidas pela comparação da coluna `Grupo` com cada categoria. `args.saida.resolve()` mostra o caminho absoluto do arquivo gerado.

O arredondamento é aplicado separadamente em cada dia. Se vários dias tiverem totais ímpares, a soma de Teste pode ficar maior que a metade arredondada do total geral. Por exemplo, dois dias com 5 linhas cada produzem 6 Teste e 4 Controle.

## 25. Dados preservados e transformações

O resultado mantém:

- Todas as linhas, incluindo registros repetidos.
- A ordem original das linhas.
- Todas as colunas da tabela carregada.
- Os valores originais da coluna de data; as datas convertidas são usadas apenas no agrupamento.

As transformações explícitas são:

1. Remoção de espaços nas extremidades dos nomes das colunas.
2. Conversão do CPF para texto, remoção de espaços nas extremidades e preenchimento com zeros quando aplicável.
3. Criação ou substituição da coluna `Grupo`.

Além disso, todas as colunas são carregadas como texto. Assim, o arquivo de saída preserva os valores lidos, mas não necessariamente os tipos de célula ou a apresentação visual do Excel original.

## 26. Fluxo completo resumido

```text
Executar main.py
    ↓
Ler argumentos do terminal
    ↓
Receber ou gerar a semente
    ↓
Definir o caminho de saída
    ↓
Ler a tabela de CSV ou da primeira planilha do Excel
    ↓
Limpar os nomes das colunas
    ↓
Validar e interpretar a coluna de data
    ↓
Agrupar as linhas pelo dia, desconsiderando o horário
    ↓
Inicializar todas as linhas como Controle
    ↓
Sortear metade de cada dia, arredondada para cima
    ↓
Marcar as posições sorteadas como Teste
    ↓
Copiar a tabela completa e tratar o CPF como texto
    ↓
Adicionar a coluna Grupo
    ↓
Exportar todas as linhas para CSV ou Excel
    ↓
Mostrar total, Teste, Controle e caminho de saída
```
