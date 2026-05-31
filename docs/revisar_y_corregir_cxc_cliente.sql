/*
    Revisa y corrige CxC de UN cliente.

    Ajusta @id_sn con el codigo del cliente.

    El script muestra:
    - Resumen real segun facturas abiertas.
    - Historial de facturas.
    - Historial de pagos/recibos.
    - Relacion CAB_ED / DET_ED del cliente.
    - Movimientos esperados vs ED existente.
    - CAB_ED cancelado con pago activo.
    - Pago cancelado con CAB_ED abierto.
    - Lineas DET_ED con montos distintos a la factura o pago real.

    Por defecto NO guarda cambios. Cambia @aplicar = 1 para corregir:
    - Reabre CAB_ED RI cancelados cuando el recibo existe y no esta cancelado.
    - Cancela CAB_ED RI abiertos cuando el recibo esta cancelado.
    - Ajusta DET_ED.DEBITO/CREDITO segun facturas y pagos.
    - Ajusta CAB_ED.TOTAL_DOC segun el monto real del movimiento.

    Esquema usado:
    CAB_ED: NO_ED, TIPO_DOC, ORIGEN, ESTATUS, TOTAL_DOC
    DET_ED: NO_ED, ID_SN, DEBITO, CREDITO
    CAB_FACTURA: ID_DOC, ID_SN, EST_DOC, TOTAL_DOC
    CAB_RECIBO_INGRESO: ID_RECIBO, EST_DOC
    DET_RECIBO_INGRESO: ID_RECIBO, NO_DOC, TOTAL_PAGO, DESCUENTO
*/

SET NOCOUNT ON;

DECLARE @id_sn VARCHAR(255) = 'CTP0042'; -- Cambiar por el cliente a revisar.
DECLARE @aplicar BIT = 1; -- 0 = preview/rollback, 1 = guardar cambios.
DECLARE @tolerancia DECIMAL(19, 4) = 0.01;

SET @id_sn = LTRIM(RTRIM(@id_sn)) COLLATE DATABASE_DEFAULT;

IF OBJECT_ID('tempdb..#facturas') IS NOT NULL DROP TABLE #facturas;
IF OBJECT_ID('tempdb..#pagos') IS NOT NULL DROP TABLE #pagos;
IF OBJECT_ID('tempdb..#ed_cliente') IS NOT NULL DROP TABLE #ed_cliente;
IF OBJECT_ID('tempdb..#esperado') IS NOT NULL DROP TABLE #esperado;
IF OBJECT_ID('tempdb..#ed_match') IS NOT NULL DROP TABLE #ed_match;
IF OBJECT_ID('tempdb..#corregir_det') IS NOT NULL DROP TABLE #corregir_det;
IF OBJECT_ID('tempdb..#corregir_cab') IS NOT NULL DROP TABLE #corregir_cab;
IF OBJECT_ID('tempdb..#reabrir_cab') IS NOT NULL DROP TABLE #reabrir_cab;
IF OBJECT_ID('tempdb..#cancelar_cab') IS NOT NULL DROP TABLE #cancelar_cab;

SELECT
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_DOC))) COLLATE DATABASE_DEFAULT AS id_doc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT AS id_sn,
    UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), f.EST_DOC), '')))) COLLATE DATABASE_DEFAULT AS estado_factura,
    CAST(ISNULL(f.TOTAL_DOC, 0) AS DECIMAL(19, 4)) AS total_doc
INTO #facturas
FROM dbo.CAB_FACTURA f
WHERE LTRIM(RTRIM(CONVERT(VARCHAR(255), f.ID_SN))) COLLATE DATABASE_DEFAULT = @id_sn;

SELECT
    LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT AS id_recibo,
    UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), r.EST_DOC), '')))) COLLATE DATABASE_DEFAULT AS estado_recibo,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.NO_DOC))) COLLATE DATABASE_DEFAULT AS no_doc,
    f.id_sn,
    CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4)) AS total_pago,
    CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4)) AS descuento,
    CAST(ISNULL(dr.TOTAL_PAGO, 0) AS DECIMAL(19, 4))
        + CAST(ISNULL(dr.DESCUENTO, 0) AS DECIMAL(19, 4)) AS total_aplicado
INTO #pagos
FROM dbo.DET_RECIBO_INGRESO dr
INNER JOIN dbo.CAB_RECIBO_INGRESO r
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), r.ID_RECIBO))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.ID_RECIBO))) COLLATE DATABASE_DEFAULT
INNER JOIN #facturas f
    ON f.id_doc = LTRIM(RTRIM(CONVERT(VARCHAR(255), dr.NO_DOC))) COLLATE DATABASE_DEFAULT;

SELECT
    LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT AS no_ed,
    UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.TIPO_DOC)))) COLLATE DATABASE_DEFAULT AS tipo_doc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), c.ORIGEN))) COLLATE DATABASE_DEFAULT AS origen,
    UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.ESTATUS), '')))) COLLATE DATABASE_DEFAULT AS estado_cab_ed,
    CAST(ISNULL(c.TOTAL_DOC, 0) AS DECIMAL(19, 4)) AS total_cab_ed,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT AS id_sn,
    CAST(ISNULL(d.DEBITO, 0) AS DECIMAL(19, 4)) AS debito_det_ed,
    CAST(ISNULL(d.CREDITO, 0) AS DECIMAL(19, 4)) AS credito_det_ed
INTO #ed_cliente
FROM dbo.CAB_ED c
INNER JOIN dbo.DET_ED d
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), d.NO_ED))) COLLATE DATABASE_DEFAULT
WHERE LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT = @id_sn;

CREATE TABLE #esperado (
    tipo_doc VARCHAR(20) COLLATE DATABASE_DEFAULT NOT NULL,
    origen VARCHAR(255) COLLATE DATABASE_DEFAULT NOT NULL,
    id_sn VARCHAR(255) COLLATE DATABASE_DEFAULT NOT NULL,
    estado_fuente VARCHAR(80) COLLATE DATABASE_DEFAULT NOT NULL,
    debito_esperado DECIMAL(19, 4) NOT NULL,
    credito_esperado DECIMAL(19, 4) NOT NULL,
    total_cab_esperado DECIMAL(19, 4) NOT NULL
);

INSERT INTO #esperado (tipo_doc, origen, id_sn, estado_fuente, debito_esperado, credito_esperado, total_cab_esperado)
SELECT
    'FC',
    id_doc,
    id_sn,
    estado_factura,
    CASE WHEN estado_factura <> 'CANCELADO' THEN total_doc ELSE 0 END,
    0,
    ABS(CASE WHEN estado_factura <> 'CANCELADO' THEN total_doc ELSE 0 END)
FROM #facturas;

INSERT INTO #esperado (tipo_doc, origen, id_sn, estado_fuente, debito_esperado, credito_esperado, total_cab_esperado)
SELECT
    'RI',
    id_recibo,
    id_sn,
    MAX(estado_recibo),
    0,
    CASE WHEN MAX(estado_recibo) <> 'CANCELADO' THEN SUM(total_aplicado) ELSE 0 END,
    ABS(CASE WHEN MAX(estado_recibo) <> 'CANCELADO' THEN SUM(total_aplicado) ELSE 0 END)
FROM #pagos
GROUP BY id_recibo, id_sn;

SELECT
    e.tipo_doc,
    e.origen,
    e.id_sn,
    e.estado_fuente,
    ed.no_ed,
    ed.estado_cab_ed,
    ed.total_cab_ed,
    ed.debito_det_ed,
    ed.credito_det_ed,
    e.debito_esperado,
    e.credito_esperado,
    e.total_cab_esperado,
    CASE
        WHEN ed.no_ed IS NULL THEN 'SIN_CAB_DET_ED'
        WHEN e.estado_fuente = 'CANCELADO' AND ed.estado_cab_ed <> 'CANCELADO' THEN 'FUENTE_CANCELADA_ED_ABIERTO'
        WHEN e.estado_fuente <> 'CANCELADO' AND ed.estado_cab_ed = 'CANCELADO' THEN 'FUENTE_ACTIVA_ED_CANCELADO'
        WHEN ABS(ISNULL(ed.debito_det_ed, 0) - e.debito_esperado) > @tolerancia
          OR ABS(ISNULL(ed.credito_det_ed, 0) - e.credito_esperado) > @tolerancia THEN 'MONTO_DET_ED_DISTINTO'
        WHEN ABS(ISNULL(ed.total_cab_ed, 0) - e.total_cab_esperado) > @tolerancia THEN 'TOTAL_CAB_ED_DISTINTO'
        ELSE 'OK'
    END AS diagnostico
INTO #ed_match
FROM #esperado e
LEFT JOIN #ed_cliente ed
    ON ed.tipo_doc = e.tipo_doc
   AND ed.origen = e.origen
   AND ed.id_sn = e.id_sn;

SELECT *
INTO #corregir_det
FROM #ed_match
WHERE no_ed IS NOT NULL
  AND estado_fuente <> 'CANCELADO'
  AND estado_cab_ed <> 'CANCELADO'
  AND (
        ABS(ISNULL(debito_det_ed, 0) - debito_esperado) > @tolerancia
     OR ABS(ISNULL(credito_det_ed, 0) - credito_esperado) > @tolerancia
  );

SELECT *
INTO #corregir_cab
FROM #ed_match
WHERE no_ed IS NOT NULL
  AND estado_fuente <> 'CANCELADO'
  AND (
        estado_cab_ed <> 'CANCELADO'
     OR diagnostico = 'FUENTE_ACTIVA_ED_CANCELADO'
  )
  AND ABS(ISNULL(total_cab_ed, 0) - total_cab_esperado) > @tolerancia;

SELECT *
INTO #reabrir_cab
FROM #ed_match
WHERE no_ed IS NOT NULL
  AND estado_fuente <> 'CANCELADO'
  AND estado_cab_ed = 'CANCELADO';

SELECT *
INTO #cancelar_cab
FROM #ed_match
WHERE no_ed IS NOT NULL
  AND estado_fuente = 'CANCELADO'
  AND estado_cab_ed <> 'CANCELADO';

SELECT
    @id_sn AS id_sn,
    SUM(CASE WHEN estado_factura <> 'CANCELADO' THEN total_doc ELSE 0 END) AS total_facturas_no_canceladas,
    (SELECT ISNULL(SUM(CASE WHEN estado_recibo <> 'CANCELADO' THEN total_aplicado ELSE 0 END), 0) FROM #pagos) AS total_pagos_no_cancelados,
    SUM(CASE WHEN estado_factura <> 'CANCELADO' THEN total_doc ELSE 0 END)
        - (SELECT ISNULL(SUM(CASE WHEN estado_recibo <> 'CANCELADO' THEN total_aplicado ELSE 0 END), 0) FROM #pagos) AS balance_real_cliente,
    (SELECT ISNULL(SUM(CASE WHEN estado_cab_ed <> 'CANCELADO' THEN debito_det_ed - credito_det_ed ELSE 0 END), 0) FROM #ed_cliente) AS balance_ed_actual
FROM #facturas;

SELECT 'FACTURAS_CLIENTE' AS etapa, *
FROM #facturas
ORDER BY id_doc;

SELECT 'PAGOS_CLIENTE' AS etapa, *
FROM #pagos
ORDER BY id_recibo, no_doc;

SELECT 'CAB_DET_ED_CLIENTE' AS etapa, *
FROM #ed_cliente
ORDER BY tipo_doc, origen, no_ed;

SELECT 'ESPERADO_VS_ED' AS etapa, *
FROM #ed_match
ORDER BY
    CASE diagnostico WHEN 'OK' THEN 2 ELSE 1 END,
    tipo_doc,
    origen;

SELECT 'CAB_ED_CANCELADO_PERO_FUENTE_ACTIVA_A_REABRIR' AS etapa, *
FROM #reabrir_cab
ORDER BY tipo_doc, origen, no_ed;

SELECT 'FUENTE_CANCELADA_PERO_CAB_ED_ABIERTO_A_CANCELAR' AS etapa, *
FROM #cancelar_cab
ORDER BY tipo_doc, origen, no_ed;

SELECT 'DET_ED_CON_MONTO_DISTINTO_A_CORREGIR' AS etapa, *
FROM #corregir_det
ORDER BY tipo_doc, origen, no_ed;

SELECT 'CAB_ED_TOTAL_DISTINTO_A_CORREGIR' AS etapa, *
FROM #corregir_cab
ORDER BY tipo_doc, origen, no_ed;

SELECT
    (SELECT COUNT(*) FROM #facturas) AS facturas_cliente,
    (SELECT COUNT(*) FROM #pagos) AS lineas_pago_cliente,
    (SELECT COUNT(*) FROM #ed_cliente) AS lineas_ed_cliente,
    (SELECT COUNT(*) FROM #ed_match WHERE diagnostico <> 'OK') AS inconsistencias_detectadas,
    (SELECT COUNT(*) FROM #reabrir_cab) AS cab_ed_cancelados_a_reabrir,
    (SELECT COUNT(*) FROM #cancelar_cab) AS cab_ed_abiertos_a_cancelar,
    (SELECT COUNT(*) FROM #corregir_det) AS det_ed_montos_a_corregir,
    (SELECT COUNT(*) FROM #corregir_cab) AS cab_ed_totales_a_corregir;

BEGIN TRANSACTION;

UPDATE c
SET c.ESTATUS = 'Abierto',
    c.TOTAL_DOC = r.total_cab_esperado
FROM dbo.CAB_ED c
INNER JOIN #reabrir_cab r
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), r.no_ed))) COLLATE DATABASE_DEFAULT;

UPDATE c
SET c.ESTATUS = 'Cancelado'
FROM dbo.CAB_ED c
INNER JOIN #cancelar_cab x
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), x.no_ed))) COLLATE DATABASE_DEFAULT;

UPDATE d
SET d.DEBITO = x.debito_esperado,
    d.CREDITO = x.credito_esperado
FROM dbo.DET_ED d
INNER JOIN #corregir_det x
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), d.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), x.no_ed))) COLLATE DATABASE_DEFAULT
   AND LTRIM(RTRIM(CONVERT(VARCHAR(255), d.ID_SN))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), x.id_sn))) COLLATE DATABASE_DEFAULT;

UPDATE c
SET c.TOTAL_DOC = x.total_cab_esperado
FROM dbo.CAB_ED c
INNER JOIN #corregir_cab x
    ON LTRIM(RTRIM(CONVERT(VARCHAR(255), c.NO_ED))) COLLATE DATABASE_DEFAULT =
       LTRIM(RTRIM(CONVERT(VARCHAR(255), x.no_ed))) COLLATE DATABASE_DEFAULT;

IF @aplicar = 1
BEGIN
    COMMIT TRANSACTION;
    SELECT 'COMMIT realizado. Cambios guardados para el cliente.' AS resultado;
END
ELSE
BEGIN
    ROLLBACK TRANSACTION;
    SELECT 'ROLLBACK realizado. No se guardo ningun cambio. Cambia @aplicar a 1 para confirmar.' AS resultado;
END;
