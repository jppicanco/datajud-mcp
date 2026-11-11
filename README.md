# datajud-mcp

Conector **MCP** de exemplo que deixa o **Claude** consultar processos judiciais na
**API Pública do DataJud**, do Conselho Nacional de Justiça.

Feito para a **aula 8 do curso de Claude Code para Defensores** (ANADEF, novembro de 2026),
para mostrar, num projeto pequeno, o caminho inteiro:

1. o CNJ oferece uma **API** (um balcão onde um programa pede e outro responde);
2. este projeto transforma esse balcão num **conector MCP** (a tomada padrão que o Claude sabe usar);
3. o conector fica no **GitHub**, e qualquer pessoa o instala pedindo ao Claude.

## O que ele faz

Uma ferramenta só, `consultar_processo`: recebe o número do processo no padrão do CNJ,
descobre o tribunal pelo próprio número e devolve os dados de capa (classe, assuntos,
órgão julgador, grau, datas) e os últimos andamentos.

Atende a Justiça Federal (TRF1 a TRF6), a Estadual (todos os TJs) e a do Trabalho.

## O que ele não faz

- Não entra em sistema nenhum com login e não pede senha.
- Não lê documento do processo: só os metadados que o CNJ já publica.
- Não grava nada.

Os dados vêm do DataJud, que pode estar alguns dias atrás do sistema do tribunal. Para
qualquer uso em peça, confira no sistema do tribunal.

## A chave

A API Pública do DataJud pede uma chave, mas a chave é **pública**: o próprio CNJ a divulga
na [documentação da API](https://datajud-wiki.cnj.jus.br/api-publica/acesso). Ela já vem no
programa. Se o CNJ trocar a chave, defina a variável de ambiente `DATAJUD_CHAVE` com a nova.

Chaves que **não** são públicas nunca devem ir para o GitHub.

## Como instalar

Abra o Claude na pasta onde quer o conector e peça:

> Quero instalar o projeto https://github.com/jppicanco/datajud-mcp nesta pasta.
> Antes de instalar, leia o README e o server.py e me diga em português simples o que ele
> faz, o que acessa e se manda algum dado meu para fora. Depois instale, cadastre o conector
> no .mcp.json desta pasta e teste.

Depois, abra **uma conversa nova** (configuração nova só vale em conversa nova) e pergunte,
por exemplo: *qual é a classe e quais são os últimos andamentos do processo 5027836-02.2024.4.04.7200?*

### Se preferir fazer à mão

Precisa do Python 3.10 ou mais novo.

```bash
git clone https://github.com/jppicanco/datajud-mcp
pip install -r datajud-mcp/requirements.txt
```

E no `.mcp.json` da pasta onde você usa o Claude (no Windows, troque `python` por `py` e
acrescente `"-3"` antes do caminho):

```json
{
  "mcpServers": {
    "datajud": {
      "type": "stdio",
      "command": "python",
      "args": ["caminho/para/datajud-mcp/server.py"]
    }
  }
}
```

## Licença

MIT. Use, copie e adapte à vontade.
