WITH facturas AS (
    SELECT 
        ID_SN,
        SUM(saldo) AS balance_fact
    FROM CAB_FACTURA
    WHERE EST_DOC = 'Abierto'
    GROUP BY ID_SN
),
ed AS (
    SELECT 
        ID_SN,
        SUM(debito) - SUM(credito) AS balance_ed
    FROM DET_ED
    GROUP BY ID_SN
)
SELECT 
    f.ID_SN,
    e.balance_ed,
    f.balance_fact
FROM facturas f
INNER JOIN ed e
    ON f.ID_SN = e.ID_SN
WHERE e.balance_ed <> f.balance_fact;

