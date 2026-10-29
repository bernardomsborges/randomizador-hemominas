import argparse
from pathlib import Path

import pandas as pd
import numpy as np


def selecionar_metade_por_dia(df, coluna_data="Data de envio da notificação", seed=None):
    """Retorna todas as linhas, classificadas em Teste ou Controle por dia."""
    if coluna_data not in df.columns:
        raise ValueError(f"Coluna não encontrada: {coluna_data}")

    valores = df[coluna_data].astype("string").str.strip()
    formato_iso = valores.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
    datas = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    # Datas ISO usam ano-mês-dia; datas brasileiras usam dia/mês/ano.
    datas.loc[formato_iso] = pd.to_datetime(
        valores.loc[formato_iso], format="ISO8601", errors="raise"
    )
    datas.loc[~formato_iso] = pd.to_datetime(
        valores.loc[~formato_iso], format="mixed", dayfirst=True, errors="raise"
    )
    if datas.isna().any():
        raise ValueError(f"Existem datas vazias na coluna {coluna_data}.")

    if seed is None:
        seed = int(np.random.default_rng().integers(0, 2**32))

    # Agrupa pelo dia, mesmo quando a data contém horário.
    # Usa posições únicas para distinguir linhas mesmo com índices repetidos.
    grupos = df.reset_index(drop=True).groupby(
        datas.reset_index(drop=True).dt.normalize(), sort=True
    )
    classificacao = np.full(len(df), "Controle", dtype=object)
    for _, grupo in grupos:
        selecionados = grupo.sample(n=(len(grupo) + 1) // 2, random_state=seed)
        classificacao[selecionados.index.to_numpy()] = "Teste"

    resultado = df.copy()
    if "CPF" in resultado.columns:
        cpf = resultado["CPF"].astype("string").str.strip()
        # Recupera zeros à esquerda de CPFs armazenados como números no Excel.
        numericos = cpf.str.fullmatch(r"[0-9]{1,11}", na=False)
        cpf.loc[numericos] = cpf.loc[numericos].str.zfill(11)
        resultado["CPF"] = cpf
    resultado["Grupo"] = classificacao
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Divide as linhas por dia em Teste e Controle.")
    parser.add_argument("entrada", type=Path, help="Arquivo CSV ou XLSX")
    parser.add_argument("--saida", type=Path, default=None)
    parser.add_argument("--coluna-data", default="Data de envio da notificação")
    parser.add_argument("--seed", type=int, default=None, help="Semente do sorteio (padrão: aleatória)")
    args = parser.parse_args()

    seed = args.seed
    if seed is None:
        seed = int(np.random.default_rng().integers(0, 2**32))
    print(f"Semente do sorteio: {seed}")
    if args.saida is None:
        args.saida = Path(f"selecionados-{seed}.csv")

    # CPF é lido como texto para preservar zeros à esquerda.
    if args.entrada.suffix.lower() == ".xlsx":
        df = pd.read_excel(args.entrada, dtype=str)
    else:
        df = pd.read_csv(args.entrada, sep=None, engine="python", dtype=str)

    df.columns = df.columns.str.strip()
    resultado = selecionar_metade_por_dia(df, args.coluna_data, seed)

    if args.saida.suffix.lower() == ".xlsx":
        resultado.to_excel(args.saida, index=False)
    else:
        resultado.to_csv(args.saida, sep=";", index=False, encoding="utf-8-sig")

    print(f"Total: {len(resultado)} linhas.")
    print(f"Teste: {(resultado['Grupo'] == 'Teste').sum()} linhas.")
    print(f"Controle: {(resultado['Grupo'] == 'Controle').sum()} linhas.")
    print(f"Arquivo salvo em: {args.saida.resolve()}")


if __name__ == "__main__":
    main()
