from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# Configuração da conexão com o banco de dados
conn_str = (
    'DRIVER={SQL Server};'
    'SERVER=WIN-9HV3FKMRQH3;'
    'DATABASE=SysacME;'
    'UID=sa;'
    'PWD=masterkey'
)

@app.route('/')
def index():
    date_filter = request.args.get('date', '15/10/2024')
    code_filter = request.args.get('code', '')

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Consulta para unir Transferências e Prevenda, ordenar por entrega
    query = '''
        SELECT 
            DISTINCT A.LOJCOD AS 'LOJA', 
            CAST(A.TRPCOD AS INT) AS 'CÓDIGO', 
            CONVERT(VARCHAR, B.TRPDATEMI, 103) AS 'EMISSÃO', 
            C.AGEDES AS 'CLIENTE', 
            D.FUNDES AS 'VENDEDOR', 
            CASE 
                WHEN PREVENDA.PRVDATETG IS NULL THEN 0 
                ELSE 1 
            END AS OrdemEntrega,
            CONVERT(VARCHAR, PREVENDA.PRVDATETG, 103) AS 'ENTREGA', 
            PREVENDA.PRVINFCOMP AS 'INFORMAÇÃO',
            B.TRPOBS AS 'PREVENDA',
            PREVENDA.PRVDATETG  -- Garantir que PRVDATETG está na lista de seleção
        FROM SysacME.dbo.ITEM_TRANSFERENCIA_PRODUTO A
        JOIN SysacME.dbo.TRANSFERENCIA_PRODUTO B ON A.LOJCOD = B.LOJCOD AND A.TRPCOD = B.TRPCOD
        JOIN SysacME.dbo.PREVENDA PREVENDA ON B.TRPOBS = CAST(PREVENDA.PRVCOD AS VARCHAR)
        JOIN SysacME.dbo.CLIENTE CLIENTE ON CLIENTE.CLICOD = PREVENDA.CLICOD
        JOIN SysacME.dbo.AGENTE C ON C.AGECOD = CLIENTE.AGECOD
        JOIN SysacME.dbo.FUNCIONARIO D ON B.TRPFUNSOL = D.FUNCOD
        WHERE B.TRPDATEMI = ?
        GROUP BY A.LOJCOD, A.TRPCOD, B.TRPDATEMI, C.AGEDES, D.FUNDES, PREVENDA.PRVDATETG, PREVENDA.PRVINFCOMP, B.TRPOBS
        ORDER BY 
            OrdemEntrega ASC, 
            PREVENDA.PRVDATETG ASC
    '''
    params = [date_filter]

    cursor.execute(query, params)
    registros = cursor.fetchall()

    # Consulta PRODUTOS com filtro de data e código
    query_produtos = '''
        SELECT A.LOJCOD AS 'LOJA', CONVERT(NUMERIC(18), A.TRPCOD) AS 'CÓDIGO', B.TRPDATEMI AS 'EMISSÃO', 
               D.FUNDES AS 'VENDEDOR', CONVERT(NUMERIC(18), C.REFCOD) AS 'PLU', C.REFDES AS 'PRODUTO', 
               A.ITPQTD QUANTIDADE, B.TRPOBS AS 'OBSERVAÇÃO'
        FROM SysacME.dbo.ITEM_TRANSFERENCIA_PRODUTO A
        JOIN SysacME.dbo.TRANSFERENCIA_PRODUTO B ON A.LOJCOD=B.LOJCOD AND A.TRPCOD=B.TRPCOD
        JOIN SysacME.dbo.REFERENCIA C ON A.REFPLU=C.REFPLU
        JOIN SysacME.dbo.FUNCIONARIO D ON B.TRPFUNSOL=D.FUNCOD
        WHERE B.TRPDATEMI = ?
    '''
    params_produtos = [date_filter]

    if code_filter:
        query_produtos += ' AND CAST(A.TRPCOD AS INT) = ?'
        params_produtos.append(code_filter)

    cursor.execute(query_produtos, params_produtos)
    produtos = cursor.fetchall()

    conn.close()

    return render_template('index.html', registros=registros, produtos=produtos, date_filter=date_filter, code_filter=code_filter)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

