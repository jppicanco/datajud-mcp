"""
datajud-mcp: conector MCP de exemplo que consulta processos na API Pública do DataJud (CNJ).

Feito para a aula 8 do curso de Claude Code para Defensores (ANADEF, novembro de 2026),
para mostrar o caminho completo: uma API pública vira um conector (MCP) que o Claude usa
sozinho, e o conector vem de um projeto no GitHub.

O que ele faz: recebe o número de um processo no padrão do CNJ, descobre o tribunal pelo
próprio número e pergunta à API pública do DataJud. Devolve os dados de capa (classe,
assuntos, órgão julgador, grau, datas) e os últimos andamentos.

O que ele NÃO faz: não entra em sistema nenhum com login, não lê documento do processo,
não grava nada. Só lê dados públicos de metadados que o CNJ já publica.

A chave usada é a chave pública que o próprio CNJ divulga na documentação da API Pública
do DataJud (https://datajud-wiki.cnj.jus.br/api-publica/acesso). Se o CNJ trocar a chave,
basta definir a variável de ambiente DATAJUD_CHAVE com a nova.

Só depende do pacote `mcp`; o resto é biblioteca padrão do Python.
"""

import json
import os
import re
import urllib.error
import urllib.request

from mcp.server.fastmcp import FastMCP

CHAVE_PUBLICA_CNJ = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
ENDERECO = "https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search"
TEMPO_LIMITE = 90  # segundos: a API pública costuma levar de 20 a 40 s por consulta

# Justiça Estadual (segmento 8): código do tribunal no número -> sigla do TJ
TJ_POR_CODIGO = {
    "01": "tjac", "02": "tjal", "03": "tjap", "04": "tjam", "05": "tjba", "06": "tjce",
    "07": "tjdft", "08": "tjes", "09": "tjgo", "10": "tjma", "11": "tjmt", "12": "tjms",
    "13": "tjmg", "14": "tjpa", "15": "tjpb", "16": "tjpr", "17": "tjpe", "18": "tjpi",
    "19": "tjrj", "20": "tjrn", "21": "tjrs", "22": "tjro", "23": "tjrr", "24": "tjsc",
    "25": "tjse", "26": "tjsp", "27": "tjto",
}

mcp = FastMCP("datajud")


def _so_digitos(numero: str) -> str:
    return re.sub(r"\D", "", numero or "")


def _tribunal(numero20: str) -> str:
    """Descobre o tribunal pelo número CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO."""
    segmento, codigo = numero20[13], numero20[14:16]
    if segmento == "4":
        return f"trf{int(codigo)}"
    if segmento == "8" and codigo in TJ_POR_CODIGO:
        return TJ_POR_CODIGO[codigo]
    if segmento == "5":
        return f"trt{int(codigo)}"
    raise ValueError(
        "Este conector de exemplo atende Justiça Federal, Estadual e do Trabalho "
        f"(o número indica o segmento {segmento}, tribunal {codigo})."
    )


def _perguntar(alias: str, numero20: str) -> list:
    corpo = json.dumps({"size": 10, "query": {"match": {"numeroProcesso": numero20}}}).encode("utf-8")
    pedido = urllib.request.Request(
        ENDERECO.format(alias=alias),
        data=corpo,
        headers={
            "Authorization": "APIKey " + os.environ.get("DATAJUD_CHAVE", CHAVE_PUBLICA_CNJ),
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
        return json.load(resposta)["hits"]["hits"]


def _data(texto: str) -> str:
    """'2024-09-21T05:00:23.000Z' ou '20240921050023' -> '21/09/2024'."""
    d = _so_digitos(texto)[:8]
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}" if len(d) == 8 else (texto or "?")


def _resumo(fonte: dict, quantos: int) -> str:
    assuntos = ", ".join(a.get("nome", "?") for a in fonte.get("assuntos", []) if isinstance(a, dict))
    linhas = [
        f"Grau: {fonte.get('grau', '?')}",
        f"Classe: {fonte.get('classe', {}).get('nome', '?')}",
        f"Assuntos: {assuntos or '?'}",
        f"Órgão julgador: {fonte.get('orgaoJulgador', {}).get('nome', '?')}",
        f"Ajuizamento: {_data(fonte.get('dataAjuizamento', ''))}",
        f"Última atualização no DataJud: {_data(fonte.get('dataHoraUltimaAtualizacao', ''))}",
        f"Últimos {quantos} andamentos (do mais recente para o mais antigo):",
    ]
    movimentos = sorted(fonte.get("movimentos", []), key=lambda m: m.get("dataHora", ""), reverse=True)
    for m in movimentos[:quantos]:
        linhas.append(f"  - {_data(m.get('dataHora', ''))}: {m.get('nome', '?')}")
    return "\n".join(linhas)


@mcp.tool()
def consultar_processo(numero: str, quantos_andamentos: int = 5) -> str:
    """
    Consulta um processo judicial na API Pública do DataJud (CNJ), só com dados públicos.

    Use quando o Defensor pedir a capa, a classe, o assunto, o órgão julgador ou os últimos
    andamentos de um processo pelo número.

    Args:
        numero: número do processo no padrão CNJ, com ou sem pontuação
                (ex.: 5027836-02.2024.4.04.7200).
        quantos_andamentos: quantos andamentos recentes mostrar (padrão 5).

    Returns:
        Texto com o tribunal e, para cada grau em que o processo aparece, classe, assuntos,
        órgão julgador, datas e os últimos andamentos. Fonte: DataJud/CNJ, que pode estar
        alguns dias atrás do sistema do tribunal.
    """
    numero20 = _so_digitos(numero)
    if len(numero20) != 20:
        return "Número inválido: o padrão CNJ tem 20 dígitos (NNNNNNN-DD.AAAA.J.TR.OOOO)."
    try:
        alias = _tribunal(numero20)
    except ValueError as erro:
        return str(erro)
    try:
        achados = _perguntar(alias, numero20)
    except urllib.error.HTTPError as erro:
        return f"O DataJud recusou a consulta (HTTP {erro.code}). Se for 401 ou 403, a chave pública pode ter mudado."
    except Exception as erro:  # rede, tempo esgotado
        return f"Não consegui falar com o DataJud ({type(erro).__name__}). Tente de novo em instantes."
    if not achados:
        return f"Nada encontrado no DataJud para {numero} em {alias.upper()}."
    partes = [f"Processo {numero} · {alias.upper()} · fonte: API Pública do DataJud (CNJ)"]
    partes += [_resumo(h["_source"], max(1, min(quantos_andamentos, 30))) for h in achados]
    return "\n\n".join(partes)


if __name__ == "__main__":
    mcp.run()
