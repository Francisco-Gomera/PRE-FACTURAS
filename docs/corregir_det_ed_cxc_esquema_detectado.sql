/*
    Correccion CxC DET_ED segun el esquema detectado en esta base:

    CAB_ED: NO_ED, TIPO_DOC, ORIGEN, ESTATUS, TOTAL_DOC
    DET_ED: NO_ED, ID_SN, DEBITO, CREDITO
    CAB_FACTURA: ID_DOC, ID_SN, EST_DOC, TOTAL_DOC
    CAB_RECIBO_INGRESO: ID_RECIBO, EST_DOC
    DET_RECIBO_INGRESO: ID_RECIBO, NO_DOC, TOTAL_PAGO, DESCUENTO

    Por defecto hace ROLLBACK. Cambia @confirmar a 1 para guardar.
*/

SET NOCOUNT ON;

DECLARE @confirmar BIT = 0; -- Cambiar a 1 para guardar.
DECLARE @tolerancia DECIMAL(19, 4) = 0.01;

IF OBJECT_ID('tempdb..#clientes_incongruentes') IS NOT NULL DROP TABLE #clientes_incongruentes;
IF OBJECT_ID('tempdb..#targets') IS NOT NULL DROP TABLE #targets;
IF OBJECT_ID('tempdb..#preview') IS NOT NULL DROP TABLE #preview;
IF OBJECT_ID('tempdb..#cab_preview') IS NOT NULL DROP TABLE #cab_preview;
IF OBJECT_ID('tempdb..#cab_ed_cancelados_con_pago') IS NOT NULL DROP TABLE #cab_ed_cancelados_con_pago;

CREATE TABLE #clientes_incongruentes (
    id_sn VARCHAR(255) COLLATE DATABASE_DEFAULT NOT NULL PRIMARY KEY
);

INSERT INTO #clientes_incongruentes (id_sn)
VALUES
    ('PRP0004'), ('CTP0382'), ('CTP3671'), ('CTP3666'), ('CTP7220'), ('CTP7673'), ('CTP2402'), ('CTP5957'),
    ('CTP0282'), ('CTP7329'), ('CTP5924'), ('CTP7559'), ('CTP1159'), ('CTP7352'), ('CTP6957'), ('CTP3861'),
    ('CTP7072'), ('CTP7496'), ('CTP0042'), ('CTP7448'), ('CTP3732'), ('CTP7135'), ('CTP1779'), ('CTP3564'),
    ('CTP6863'), ('CTP1836'), ('CTP2033'), ('CTP3274'), ('CTP4142'), ('CTP7223'), ('CTP6995'), ('CTP3978'),
    ('CTP2446'), ('CTP2835'), ('CTP6706'), ('CTP2086'), ('CTP7120'), ('CTP7687'), ('CTP1131'), ('CTP6733'),
    ('CTP7603'), ('CTP0451'), ('CTP1596'), ('CTP1616'), ('CTP1783'), ('CTP3560'), ('CTP4601'), ('CTP6326'),
    ('CTP6463'), ('CTP0000'), ('CTP4202'), ('CTP7639'), ('CTP3173'), ('CTP2210'), ('CTP6869'), ('CTP4332'),
    ('CTP5736'), ('CTP0063'), ('CTP1314'), ('CTP2938'), ('CTP4567'), ('CTP2497'), ('CTP7449'), ('CTP5520'),
    ('CTP0155'), ('CTP0507'), ('CTP1584'), ('CTP2320'), ('CTP2868'), ('CTP4128'), ('CTP7294'), ('CTP7481'),
    ('CTP7624'), ('CTP2920'), ('CTP6879'), ('CTP1208'), ('CTP1253'), ('CTP1341'), ('CTP1441'), ('CTP3590'),
    ('CTP4839'), ('CTP5268'), ('CTP5564'), ('CTP5875'), ('CTP7233'), ('CTP7622'), ('CTP7623'), ('CTP2066'),
    ('CTP2228'), ('CTP2469'), ('CTP4008'), ('CTP5440'), ('CTP6763'), ('CTP6811'), ('CTP6934'), ('CTP5467'),
    ('CTP6224'), ('CTP1491'), ('CTP2901'), ('CTP4186'), ('CTP4195'), ('CTP4304'), ('CTP4443'), ('CTP4466'),
    ('CTP4549'), ('CTP4558'), ('CTP6666'), ('CTP6866'), ('CTP0067'), ('CTP0759'), ('CTP1269'), ('CTP1387'),
    ('CTP3165'), ('CTP3612'), ('CTP4370'), ('CTP4578'), ('CTP5197'), ('CTP5770'), ('CTP6169'), ('CTP6504'),
    ('CTP6918'), ('CTP7123'), ('CTP7561'), ('CTP7575'), ('CTP7726'), ('CTP7769'), ('CTP3863'), ('CTP5135'),
    ('CTP0147'), ('CTP0495'), ('CTP0596'), ('CTP1209'), ('CTP1281'), ('CTP2237'), ('CTP2811'), ('CTP3101'),
    ('CTP3280'), ('CTP5297'), ('CTP7096'), ('CTP7372'), ('CTP7430'), ('CTP7478'), ('CTP7527'), ('CTP7538'),
    ('CTP7716'), ('CTP6799'), ('CTP6838'), ('CTP5059'), ('CTP0697'), ('CTP2914'), ('CTP3768'), ('CTP3877'),
    ('CTP6166'), ('CTP5498'), ('CTP0059'), ('CTP0097'), ('CTP0645'), ('CTP1291'), ('CTP1555'), ('CTP1651'),
    ('CTP1750'), ('CTP2136'), ('CTP4252'), ('CTP4278'), ('CTP4484'), ('CTP4913'), ('CTP5083'), ('CTP5286'),
    ('CTP5616'), ('CTP6455'), ('CTP6771'), ('CTP7255'), ('CTP7767'), ('CTP6556'), ('CTP0885'), ('CTP1050'),
    ('CTP1116'), ('CTP1417'), ('CTP3205'), ('CTP3300'), ('CTP3731'), ('CTP5205'), ('CTP6142'), ('CTP6971'),
    ('CTP7375'), ('CTP3387'), ('CTP0001'), ('CTP0279'), ('CTP0439'), ('CTP1592'), ('CTP1679'), ('CTP1885'),
    ('CTP1935'), ('CTP3149'), ('CTP3286'), ('CTP3649'), ('CTP3836'), ('CTP4789'), ('CTP5020'), ('CTP5098'),
    ('CTP5151'), ('CTP5696'), ('CTP6013'), ('CTP6025'), ('CTP6055'), ('CTP6123'), ('CTP6160'), ('CTP6458'),
    ('CTP6717'), ('CTP6932'), ('CTP7268'), ('CTP4519'), ('CTP6589'), ('CTP1110'), ('CTP2100'), ('CTP2729'),
    ('CTP3085'), ('CTP3279'), ('CTP3332'), ('CTP4709'), ('CTP4961'), ('CTP6250'), ('CTP6493'), ('CTP7571'),
    ('CTP7470'), ('CTP0628'), ('CTP3249'), ('CTP7640'), ('CTP6819'), ('PRP0001'), ('CTP5543'), ('CTP4239'),
    ('CTP6834'), ('CTP2525'), ('CTP6802');

CREATE TABLE #targets (
    tipo_doc VARCHAR(20) COLLATE DATABASE_DEFAULT NOT NULL,
    origen VARCHAR(255) COLLATE DATABASE_DEFAULT NOT NULL,
    id_sn VARCHAR(255) COLLATE DATABASE_DEFAULT NOT NULL,
    debito_esperado DECIMAL(19, 4) NOT NULL,
    credito_esperado DECIMAL(19, 4) NOT NULL,
    monto_cab_esperado DECIMAL(19, 4) NOT NULL
);

INSERT INTO #targets (tipo_doc, origen, id_sn, debito_esperado, credito_esperado, monto_cab_esperado)
SELECT
    'FC' AS tipo_doc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_DOC))) COLLATE DATABASE_DEFAULT AS origen,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT AS id_sn,
    SUM(CAST(ISNULL(f.TOTAL_DOC, 0) AS DECIMAL(19, 4))) AS debito_esperado,
    0 AS credito_esperado,
    ABS(SUM(CAST(ISNULL(f.TOTAL_DOC, 0) AS DECIMAL(19, 4)))) AS monto_cab_esperado
FROM dbo.CAB_FACTURA f
WHERE LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), f.ID_DOC), ''))) <> ''
  AND LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), f.ID_SN), ''))) <> ''
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), f.EST_DOC), '')))) <> 'CANCELADO'
  AND EXISTS (
      SELECT 1
      FROM #clientes_incongruentes ci
      WHERE ci.id_sn = LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT
  )
GROUP BY
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_DOC))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN)));

INSERT INTO #targets (tipo_doc, origen, id_sn, debito_esperado, credito_esperado, monto_cab_esperado)
SELECT
    'RI' AS tipo_doc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT AS origen,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT AS id_sn,
    0 AS debito_esperado,
    SUM(
        CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4))
        + CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4))
    ) AS credito_esperado,
    ABS(SUM(
        CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4))
        + CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4))
    )) AS monto_cab_esperado
FROM dbo.DET_RECIBO_INGRESO dr
INNER JOIN dbo.CAB_RECIBO_INGRESO r
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.ID_RECIBO))) COLLATE DATABASE_DEFAULT
INNER JOIN dbo.CAB_FACTURA f
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_DOC))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.NO_DOC))) COLLATE DATABASE_DEFAULT
WHERE LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), r.ID_RECIBO), ''))) <> ''
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), r.EST_DOC), '')))) <> 'CANCELADO'
  AND EXISTS (
      SELECT 1
      FROM #clientes_incongruentes ci
      WHERE ci.id_sn = LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT
  )
GROUP BY
    LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN)));

DELETE FROM #targets
WHERE ABS(debito_esperado) <= @tolerancia
  AND ABS(credito_esperado) <= @tolerancia;

;WITH pagos_recibo AS (
    SELECT
        LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT AS id_recibo,
        LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT AS id_sn,
        COUNT(*) AS lineas_pago,
        SUM(
            CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4))
            + CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4))
        ) AS total_pago_confirmado
    FROM dbo.CAB_RECIBO_INGRESO r
    INNER JOIN dbo.DET_RECIBO_INGRESO dr
        ON LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT =
           LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.ID_RECIBO))) COLLATE DATABASE_DEFAULT
    INNER JOIN dbo.CAB_FACTURA f
        ON LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_DOC))) COLLATE DATABASE_DEFAULT =
           LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.NO_DOC))) COLLATE DATABASE_DEFAULT
    WHERE UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), r.EST_DOC), '')))) <> 'CANCELADO'
      AND EXISTS (
          SELECT 1
          FROM #clientes_incongruentes ci
          WHERE ci.id_sn = LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT
      )
    GROUP BY
        LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))),
        LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN)))
    HAVING ABS(SUM(
        CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4))
        + CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4))
    )) > @tolerancia
),
cab_cancelados AS (
    SELECT
        c.NO_ED AS cab_ed_no,
        c.TIPO_DOC,
        c.ORIGEN,
        c.ESTATUS AS estatus_actual,
        c.TOTAL_DOC AS total_doc_actual,
        p.id_recibo,
        p.id_sn,
        p.lineas_pago,
        p.total_pago_confirmado,
        ROW_NUMBER() OVER (
            PARTITION BY p.id_recibo, p.id_sn
            ORDER BY
                CASE WHEN TRY_CONVERT(BIGINT, c.NO_ED) IS NULL THEN 1 ELSE 0 END,
                TRY_CONVERT(BIGINT, c.NO_ED),
                CONVERT(VARCHAR(255), c.NO_ED)
        ) AS rn
    FROM dbo.CAB_ED c
    INNER JOIN pagos_recibo p
        ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.ORIGEN))) COLLATE DATABASE_DEFAULT = p.id_recibo
    WHERE UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.TIPO_DOC)))) = 'RI'
      AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.ESTATUS), '')))) = 'CANCELADO'
)
SELECT
    cab_ed_no,
    TIPO_DOC,
    ORIGEN,
    estatus_actual,
    total_doc_actual,
    id_recibo,
    id_sn,
    lineas_pago,
    total_pago_confirmado
INTO #cab_ed_cancelados_con_pago
FROM cab_cancelados
WHERE rn = 1;

SELECT 'CAB_ED_RI_CANCELADOS_CON_PAGO_ACTIVO_A_REABRIR' AS etapa, *
FROM #cab_ed_cancelados_con_pago
ORDER BY id_sn, id_recibo, cab_ed_no;

SELECT
    c.NO_ED AS cab_ed_no,
    d.NO_ED AS det_ed_no,
    c.TIPO_DOC AS tipo_doc_actual,
    c.ORIGEN AS origen_actual,
    d.ID_SN AS id_sn_actual,
    CAST(ISNULL(d.DEBITO, 0) AS DECIMAL(19, 4)) AS debito_actual,
    CAST(ISNULL(d.CREDITO, 0) AS DECIMAL(19, 4)) AS credito_actual,
    t.debito_esperado,
    t.credito_esperado,
    t.monto_cab_esperado
INTO #preview
FROM dbo.CAB_ED c
INNER JOIN dbo.DET_ED d
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), d.NO_ED))) COLLATE DATABASE_DEFAULT
INNER JOIN #targets t
    ON t.tipo_doc = UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.TIPO_DOC)))) COLLATE DATABASE_DEFAULT
   AND t.origen = LTRIM(RTRIM(CONVERT(VARCHAR(255), c.ORIGEN))) COLLATE DATABASE_DEFAULT
   AND t.id_sn = LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT
WHERE UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.ESTATUS), '')))) <> 'CANCELADO'
  AND (
        ABS(CAST(ISNULL(d.DEBITO, 0) AS DECIMAL(19, 4)) - t.debito_esperado) > @tolerancia
     OR ABS(CAST(ISNULL(d.CREDITO, 0) AS DECIMAL(19, 4)) - t.credito_esperado) > @tolerancia
  );

SELECT 'PREVIEW_DET_ED_A_CORREGIR' AS etapa, *
FROM #preview
ORDER BY tipo_doc_actual, origen_actual, id_sn_actual;

SELECT
    'MOVIMIENTOS_SIN_LINEA_CXC_EN_DET_ED_NO_SE_CORRIGEN_AUTOMATICO' AS etapa,
    t.tipo_doc,
    t.origen,
    t.id_sn,
    t.debito_esperado,
    t.credito_esperado
FROM #targets t
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.CAB_ED c
    INNER JOIN dbo.DET_ED d
        ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
           LTRIM(RTRIM(CONVERT(VARCHAR(255), d.NO_ED))) COLLATE DATABASE_DEFAULT
    WHERE t.tipo_doc = UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.TIPO_DOC)))) COLLATE DATABASE_DEFAULT
      AND t.origen = LTRIM(RTRIM(CONVERT(VARCHAR(255), c.ORIGEN))) COLLATE DATABASE_DEFAULT
      AND t.id_sn = LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT
      AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.ESTATUS), '')))) <> 'CANCELADO'
)
ORDER BY tipo_doc, origen, id_sn;

SELECT DISTINCT
    cab_ed_no,
    tipo_doc_actual,
    monto_cab_esperado
INTO #cab_preview
FROM #preview;

BEGIN TRANSACTION;

UPDATE d
SET d.DEBITO = p.debito_esperado,
    d.CREDITO = p.credito_esperado
FROM dbo.DET_ED d
INNER JOIN #preview p
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), d.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), p.det_ed_no))) COLLATE DATABASE_DEFAULT
   AND LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), p.id_sn_actual))) COLLATE DATABASE_DEFAULT;

UPDATE c
SET c.TOTAL_DOC = p.monto_cab_esperado
FROM dbo.CAB_ED c
INNER JOIN #cab_preview p
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), p.cab_ed_no))) COLLATE DATABASE_DEFAULT;

UPDATE c
SET c.ESTATUS = 'Abierto',
    c.TOTAL_DOC = p.total_pago_confirmado
FROM dbo.CAB_ED c
INNER JOIN #cab_ed_cancelados_con_pago p
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), p.cab_ed_no))) COLLATE DATABASE_DEFAULT
WHERE UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.ESTATUS), '')))) = 'CANCELADO';

SELECT
    (SELECT COUNT(*) FROM #clientes_incongruentes) AS clientes_excel,
    (SELECT COUNT(*) FROM #targets) AS total_movimientos_fuente,
    (SELECT COUNT(*) FROM #preview) AS total_lineas_det_ed_corregidas,
    (SELECT COUNT(*) FROM #cab_preview) AS total_cab_ed_afectados,
    (SELECT COUNT(*) FROM #cab_ed_cancelados_con_pago) AS total_cab_ed_cancelados_con_pago_a_reabrir;

IF @confirmar = 1
BEGIN
    COMMIT TRANSACTION;
    SELECT 'COMMIT realizado. Cambios guardados.' AS resultado;
END
ELSE
BEGIN
    ROLLBACK TRANSACTION;
    SELECT 'ROLLBACK realizado. No se guardo ningun cambio. Cambia @confirmar a 1 para confirmar.' AS resultado;
END;
