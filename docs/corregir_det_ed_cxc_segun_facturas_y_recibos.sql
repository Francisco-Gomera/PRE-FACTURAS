/*
    Corrige lineas CxC de DET_ED segun movimientos reales:

    - Facturas no canceladas: la linea CxC de DET_ED debe quedar con DEBITO = total de la factura.
    - Recibos activos/no cancelados: la linea CxC de DET_ED debe quedar con CREDITO =
      SUM(pago aplicado + descuento/avance aplicado).

    El script detecta variantes de columnas usadas por la aplicacion, por ejemplo:
    ID_DOC/ID_ED, NO_DOC/NO_ED, EST_DOC/ESTADO/ESTATUS, ORIGEN/REFERENCIA/NO_RECIBO,
    DEBITO/DEBE, CREDITO/HABER, TOTAL_DOC/MONTO/IMPORTE.

    Por defecto hace ROLLBACK. Cambia @confirmar a 1 para guardar.
*/

SET NOCOUNT ON;

DECLARE @confirmar BIT = 0; -- Cambiar a 1 para guardar.
DECLARE @tolerancia DECIMAL(19, 4) = 0.01;
DECLARE @schema SYSNAME = N'dbo';
DECLARE @mostrar_sql BIT = 0; -- Cambiar a 1 si SQL Server reporta otra linea de sintaxis.

DECLARE
    @cab_ed_schema SYSNAME,
    @det_ed_schema SYSNAME,
    @cab_fact_schema SYSNAME,
    @cab_rec_schema SYSNAME,
    @det_rec_schema SYSNAME,
    @cab_ed_obj NVARCHAR(300),
    @det_ed_obj NVARCHAR(300),
    @cab_fact_obj NVARCHAR(300),
    @cab_rec_obj NVARCHAR(300),
    @det_rec_obj NVARCHAR(300),
    @cab_ed NVARCHAR(300),
    @det_ed NVARCHAR(300),
    @cab_fact NVARCHAR(300),
    @cab_rec NVARCHAR(300),
    @det_rec NVARCHAR(300),
    @cab_ed_id_col SYSNAME,
    @cab_ed_no_col SYSNAME,
    @cab_ed_tipo_col SYSNAME,
    @cab_ed_origen_col SYSNAME,
    @cab_ed_estado_col SYSNAME,
    @cab_ed_total_col SYSNAME,
    @cab_ed_abono_col SYSNAME,
    @cab_ed_saldo_col SYSNAME,
    @det_ed_id_col SYSNAME,
    @det_ed_no_col SYSNAME,
    @det_ed_update_col SYSNAME,
    @det_ed_line_col SYSNAME,
    @det_ed_cliente_col SYSNAME,
    @det_ed_debito_col SYSNAME,
    @det_ed_credito_col SYSNAME,
    @fact_doc_col SYSNAME,
    @fact_cliente_col SYSNAME,
    @fact_estado_col SYSNAME,
    @fact_cancelado_col SYSNAME,
    @fact_total_col SYSNAME,
    @rec_id_col SYSNAME,
    @rec_no_col SYSNAME,
    @rec_estado_col SYSNAME,
    @rec_cancelado_col SYSNAME,
    @det_rec_id_col SYSNAME,
    @det_rec_doc_col SYSNAME,
    @det_rec_pago_col SYSNAME,
    @det_rec_desc_col SYSNAME,
    @sql NVARCHAR(MAX);

SELECT TOP 1 @cab_ed_schema = s.name
FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.name = N'CAB_ED'
ORDER BY CASE WHEN s.name = @schema THEN 0 WHEN s.name = N'dbo' THEN 1 ELSE 2 END, s.name;

SELECT TOP 1 @det_ed_schema = s.name
FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.name = N'DET_ED'
ORDER BY CASE WHEN s.name = @schema THEN 0 WHEN s.name = N'dbo' THEN 1 ELSE 2 END, s.name;

SELECT TOP 1 @cab_fact_schema = s.name
FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.name = N'CAB_FACTURA'
ORDER BY CASE WHEN s.name = @schema THEN 0 WHEN s.name = N'dbo' THEN 1 ELSE 2 END, s.name;

SELECT TOP 1 @cab_rec_schema = s.name
FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.name = N'CAB_RECIBO_INGRESO'
ORDER BY CASE WHEN s.name = @schema THEN 0 WHEN s.name = N'dbo' THEN 1 ELSE 2 END, s.name;

SELECT TOP 1 @det_rec_schema = s.name
FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.name = N'DET_RECIBO_INGRESO'
ORDER BY CASE WHEN s.name = @schema THEN 0 WHEN s.name = N'dbo' THEN 1 ELSE 2 END, s.name;

IF @cab_ed_schema IS NULL OR @det_ed_schema IS NULL OR @cab_fact_schema IS NULL OR @cab_rec_schema IS NULL OR @det_rec_schema IS NULL
BEGIN
    SELECT
        'TABLAS_DETECTADAS' AS diagnostico,
        @cab_ed_schema AS cab_ed_schema,
        @det_ed_schema AS det_ed_schema,
        @cab_fact_schema AS cab_fact_schema,
        @cab_rec_schema AS cab_rec_schema,
        @det_rec_schema AS det_rec_schema;
    RAISERROR('No se encontraron todas las tablas requeridas en la base actual.', 16, 1);
    RETURN;
END;

SET @cab_ed_obj = @cab_ed_schema + N'.CAB_ED';
SET @det_ed_obj = @det_ed_schema + N'.DET_ED';
SET @cab_fact_obj = @cab_fact_schema + N'.CAB_FACTURA';
SET @cab_rec_obj = @cab_rec_schema + N'.CAB_RECIBO_INGRESO';
SET @det_rec_obj = @det_rec_schema + N'.DET_RECIBO_INGRESO';

SET @cab_ed = QUOTENAME(@cab_ed_schema) + N'.[CAB_ED]';
SET @det_ed = QUOTENAME(@det_ed_schema) + N'.[DET_ED]';
SET @cab_fact = QUOTENAME(@cab_fact_schema) + N'.[CAB_FACTURA]';
SET @cab_rec = QUOTENAME(@cab_rec_schema) + N'.[CAB_RECIBO_INGRESO]';
SET @det_rec = QUOTENAME(@det_rec_schema) + N'.[DET_RECIBO_INGRESO]';

SET @cab_ed_id_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'ID_ED') IS NOT NULL THEN N'ID_ED' END;
SET @cab_ed_no_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'NO_ED') IS NOT NULL THEN N'NO_ED' END;
SET @cab_ed_tipo_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'TIPO_DOC') IS NOT NULL THEN N'TIPO_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'TD') IS NOT NULL THEN N'TD' WHEN COL_LENGTH(@cab_ed_obj, 'CLASE_DOC') IS NOT NULL THEN N'CLASE_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'TIPO') IS NOT NULL THEN N'TIPO' END;
SET @cab_ed_origen_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'ORIGEN') IS NOT NULL THEN N'ORIGEN' WHEN COL_LENGTH(@cab_ed_obj, 'REFERENCIA') IS NOT NULL THEN N'REFERENCIA' WHEN COL_LENGTH(@cab_ed_obj, 'NO_RECIBO') IS NOT NULL THEN N'NO_RECIBO' END;
SET @cab_ed_estado_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'EST_DOC') IS NOT NULL THEN N'EST_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'ESTADO') IS NOT NULL THEN N'ESTADO' WHEN COL_LENGTH(@cab_ed_obj, 'ESTATUS') IS NOT NULL THEN N'ESTATUS' END;
SET @cab_ed_total_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'TOTAL_DOC') IS NOT NULL THEN N'TOTAL_DOC' WHEN COL_LENGTH(@cab_ed_obj, 'MONTO') IS NOT NULL THEN N'MONTO' WHEN COL_LENGTH(@cab_ed_obj, 'IMPORTE') IS NOT NULL THEN N'IMPORTE' END;
SET @cab_ed_abono_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'ABONO') IS NOT NULL THEN N'ABONO' WHEN COL_LENGTH(@cab_ed_obj, 'PAGADO') IS NOT NULL THEN N'PAGADO' END;
SET @cab_ed_saldo_col = CASE WHEN COL_LENGTH(@cab_ed_obj, 'SALDO') IS NOT NULL THEN N'SALDO' WHEN COL_LENGTH(@cab_ed_obj, 'BALANCE') IS NOT NULL THEN N'BALANCE' END;

SET @det_ed_id_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' WHEN COL_LENGTH(@det_ed_obj, 'ID_ED') IS NOT NULL THEN N'ID_ED' END;
SET @det_ed_no_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' WHEN COL_LENGTH(@det_ed_obj, 'NO_ED') IS NOT NULL THEN N'NO_ED' END;
SET @det_ed_line_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'NO_LINEA') IS NOT NULL THEN N'NO_LINEA' WHEN COL_LENGTH(@det_ed_obj, 'LINEA') IS NOT NULL THEN N'LINEA' WHEN COL_LENGTH(@det_ed_obj, 'NO_ITEM') IS NOT NULL THEN N'NO_ITEM' WHEN COL_LENGTH(@det_ed_obj, 'ORDEN') IS NOT NULL THEN N'ORDEN' END;
SET @det_ed_cliente_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'ID_SN') IS NOT NULL THEN N'ID_SN' WHEN COL_LENGTH(@det_ed_obj, 'CLIENTE') IS NOT NULL THEN N'CLIENTE' WHEN COL_LENGTH(@det_ed_obj, 'COD_CLIENTE') IS NOT NULL THEN N'COD_CLIENTE' END;
SET @det_ed_debito_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'DEBITO') IS NOT NULL THEN N'DEBITO' WHEN COL_LENGTH(@det_ed_obj, 'DEBE') IS NOT NULL THEN N'DEBE' END;
SET @det_ed_credito_col = CASE WHEN COL_LENGTH(@det_ed_obj, 'CREDITO') IS NOT NULL THEN N'CREDITO' WHEN COL_LENGTH(@det_ed_obj, 'HABER') IS NOT NULL THEN N'HABER' END;

SET @fact_doc_col = CASE WHEN COL_LENGTH(@cab_fact_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' WHEN COL_LENGTH(@cab_fact_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' WHEN COL_LENGTH(@cab_fact_obj, 'DOCUMENTO') IS NOT NULL THEN N'DOCUMENTO' WHEN COL_LENGTH(@cab_fact_obj, 'FACTURA') IS NOT NULL THEN N'FACTURA' END;
SET @fact_cliente_col = CASE WHEN COL_LENGTH(@cab_fact_obj, 'ID_SN') IS NOT NULL THEN N'ID_SN' WHEN COL_LENGTH(@cab_fact_obj, 'CLIENTE') IS NOT NULL THEN N'CLIENTE' WHEN COL_LENGTH(@cab_fact_obj, 'COD_CLIENTE') IS NOT NULL THEN N'COD_CLIENTE' END;
SET @fact_estado_col = CASE WHEN COL_LENGTH(@cab_fact_obj, 'EST_DOC') IS NOT NULL THEN N'EST_DOC' WHEN COL_LENGTH(@cab_fact_obj, 'ESTADO') IS NOT NULL THEN N'ESTADO' WHEN COL_LENGTH(@cab_fact_obj, 'ESTATUS') IS NOT NULL THEN N'ESTATUS' END;
SET @fact_cancelado_col = CASE WHEN COL_LENGTH(@cab_fact_obj, 'CANCELADO') IS NOT NULL THEN N'CANCELADO' END;
SET @fact_total_col = CASE WHEN COL_LENGTH(@cab_fact_obj, 'TOTAL_DOC') IS NOT NULL THEN N'TOTAL_DOC' WHEN COL_LENGTH(@cab_fact_obj, 'MONTO') IS NOT NULL THEN N'MONTO' WHEN COL_LENGTH(@cab_fact_obj, 'IMPORTE') IS NOT NULL THEN N'IMPORTE' END;

SET @rec_id_col = CASE WHEN COL_LENGTH(@cab_rec_obj, 'ID_RECIBO') IS NOT NULL THEN N'ID_RECIBO' WHEN COL_LENGTH(@cab_rec_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' WHEN COL_LENGTH(@cab_rec_obj, 'NO_RECIBO') IS NOT NULL THEN N'NO_RECIBO' WHEN COL_LENGTH(@cab_rec_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' END;
SET @rec_no_col = CASE WHEN COL_LENGTH(@cab_rec_obj, 'NO_RECIBO') IS NOT NULL THEN N'NO_RECIBO' WHEN COL_LENGTH(@cab_rec_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' WHEN COL_LENGTH(@cab_rec_obj, 'ID_RECIBO') IS NOT NULL THEN N'ID_RECIBO' WHEN COL_LENGTH(@cab_rec_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' END;
SET @rec_estado_col = CASE WHEN COL_LENGTH(@cab_rec_obj, 'EST_DOC') IS NOT NULL THEN N'EST_DOC' WHEN COL_LENGTH(@cab_rec_obj, 'ESTADO') IS NOT NULL THEN N'ESTADO' WHEN COL_LENGTH(@cab_rec_obj, 'ESTATUS') IS NOT NULL THEN N'ESTATUS' END;
SET @rec_cancelado_col = CASE WHEN COL_LENGTH(@cab_rec_obj, 'CANCELADO') IS NOT NULL THEN N'CANCELADO' END;

SET @det_rec_id_col = CASE WHEN COL_LENGTH(@det_rec_obj, 'ID_RECIBO') IS NOT NULL THEN N'ID_RECIBO' WHEN COL_LENGTH(@det_rec_obj, 'NO_RECIBO') IS NOT NULL THEN N'NO_RECIBO' WHEN COL_LENGTH(@det_rec_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' END;
SET @det_rec_doc_col = CASE WHEN COL_LENGTH(@det_rec_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC' WHEN COL_LENGTH(@det_rec_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC' WHEN COL_LENGTH(@det_rec_obj, 'DOCUMENTO') IS NOT NULL THEN N'DOCUMENTO' WHEN COL_LENGTH(@det_rec_obj, 'ID_DOC_FACTURA') IS NOT NULL THEN N'ID_DOC_FACTURA' WHEN COL_LENGTH(@det_rec_obj, 'FACTURA') IS NOT NULL THEN N'FACTURA' END;
SET @det_rec_pago_col = CASE WHEN COL_LENGTH(@det_rec_obj, 'TOTAL_PAGO') IS NOT NULL THEN N'TOTAL_PAGO' WHEN COL_LENGTH(@det_rec_obj, 'TOTAL_PAGO2') IS NOT NULL THEN N'TOTAL_PAGO2' WHEN COL_LENGTH(@det_rec_obj, 'PAGO_ABONO') IS NOT NULL THEN N'PAGO_ABONO' WHEN COL_LENGTH(@det_rec_obj, 'IMP_ABONO') IS NOT NULL THEN N'IMP_ABONO' WHEN COL_LENGTH(@det_rec_obj, 'IMP_PAGADO') IS NOT NULL THEN N'IMP_PAGADO' WHEN COL_LENGTH(@det_rec_obj, 'IMP_PAGO') IS NOT NULL THEN N'IMP_PAGO' WHEN COL_LENGTH(@det_rec_obj, 'IMP_COBRADO') IS NOT NULL THEN N'IMP_COBRADO' WHEN COL_LENGTH(@det_rec_obj, 'IMP_APLICADO') IS NOT NULL THEN N'IMP_APLICADO' WHEN COL_LENGTH(@det_rec_obj, 'MONTO_APLICADO') IS NOT NULL THEN N'MONTO_APLICADO' WHEN COL_LENGTH(@det_rec_obj, 'ABONO_APLICADO') IS NOT NULL THEN N'ABONO_APLICADO' WHEN COL_LENGTH(@det_rec_obj, 'MONTO_ABONO') IS NOT NULL THEN N'MONTO_ABONO' WHEN COL_LENGTH(@det_rec_obj, 'MONTO_PAGO') IS NOT NULL THEN N'MONTO_PAGO' WHEN COL_LENGTH(@det_rec_obj, 'ABONO') IS NOT NULL THEN N'ABONO' WHEN COL_LENGTH(@det_rec_obj, 'PAGADO') IS NOT NULL THEN N'PAGADO' WHEN COL_LENGTH(@det_rec_obj, 'PAGO') IS NOT NULL THEN N'PAGO' WHEN COL_LENGTH(@det_rec_obj, 'COBRO') IS NOT NULL THEN N'COBRO' WHEN COL_LENGTH(@det_rec_obj, 'IMPORTE') IS NOT NULL THEN N'IMPORTE' END;
SET @det_rec_desc_col = CASE WHEN COL_LENGTH(@det_rec_obj, 'DESC_AVANCE') IS NOT NULL THEN N'DESC_AVANCE' WHEN COL_LENGTH(@det_rec_obj, 'DESCUENTO') IS NOT NULL THEN N'DESCUENTO' WHEN COL_LENGTH(@det_rec_obj, 'AVANCE') IS NOT NULL THEN N'AVANCE' WHEN COL_LENGTH(@det_rec_obj, 'DESC') IS NOT NULL THEN N'DESC' END;

SELECT
    'COLUMNAS_DETECTADAS' AS diagnostico,
    @cab_ed AS cab_ed,
    @det_ed AS det_ed,
    @cab_fact AS cab_factura,
    @cab_rec AS cab_recibo_ingreso,
    @det_rec AS det_recibo_ingreso,
    @cab_ed_id_col AS cab_ed_id_col,
    @cab_ed_no_col AS cab_ed_no_col,
    @cab_ed_tipo_col AS cab_ed_tipo_col,
    @cab_ed_origen_col AS cab_ed_origen_col,
    @cab_ed_estado_col AS cab_ed_estado_col,
    @cab_ed_total_col AS cab_ed_total_col,
    @cab_ed_abono_col AS cab_ed_abono_col,
    @cab_ed_saldo_col AS cab_ed_saldo_col,
    @det_ed_id_col AS det_ed_id_col,
    @det_ed_no_col AS det_ed_no_col,
    @det_ed_line_col AS det_ed_line_col,
    @det_ed_cliente_col AS det_ed_cliente_col,
    @det_ed_debito_col AS det_ed_debito_col,
    @det_ed_credito_col AS det_ed_credito_col,
    @fact_doc_col AS fact_doc_col,
    @fact_cliente_col AS fact_cliente_col,
    @fact_estado_col AS fact_estado_col,
    @fact_total_col AS fact_total_col,
    @rec_id_col AS rec_id_col,
    @rec_no_col AS rec_no_col,
    @rec_estado_col AS rec_estado_col,
    @det_rec_id_col AS det_rec_id_col,
    @det_rec_doc_col AS det_rec_doc_col,
    @det_rec_pago_col AS det_rec_pago_col,
    @det_rec_desc_col AS det_rec_desc_col;

SELECT 'COLUMNAS_OPCIONALES_NO_DETECTADAS' AS diagnostico, columna_opcional, efecto
FROM (VALUES
    (CASE WHEN @cab_ed_estado_col IS NULL THEN 'CAB_ED estado (EST_DOC/ESTADO/ESTATUS)' END, 'No se filtraran CAB_ED cancelados por estado.'),
    (CASE WHEN @det_ed_line_col IS NULL THEN 'DET_ED linea (NO_LINEA/LINEA/NO_ITEM/ORDEN)' END, 'DET_ED se actualizara por documento + cliente.'),
    (CASE WHEN @fact_estado_col IS NULL THEN 'CAB_FACTURA estado (EST_DOC/ESTADO/ESTATUS)' END, 'No se filtraran facturas canceladas por estado.'),
    (CASE WHEN @rec_estado_col IS NULL THEN 'CAB_RECIBO_INGRESO estado (EST_DOC/ESTADO/ESTATUS)' END, 'No se filtraran recibos cancelados por estado.')
) optional_missing(columna_opcional, efecto)
WHERE columna_opcional IS NOT NULL;

IF @cab_ed_tipo_col IS NULL OR @cab_ed_origen_col IS NULL
   OR @det_ed_cliente_col IS NULL OR @det_ed_debito_col IS NULL OR @det_ed_credito_col IS NULL
   OR @fact_doc_col IS NULL OR @fact_cliente_col IS NULL OR @fact_total_col IS NULL
   OR @rec_id_col IS NULL OR @rec_no_col IS NULL
   OR @det_rec_id_col IS NULL OR @det_rec_doc_col IS NULL OR @det_rec_pago_col IS NULL
BEGIN
    SELECT 'COLUMNAS_FALTANTES' AS diagnostico, requisito
    FROM (VALUES
        (CASE WHEN @cab_ed_tipo_col IS NULL THEN 'CAB_ED tipo documento (TIPO_DOC/TD/CLASE_DOC/TIPO)' END),
        (CASE WHEN @cab_ed_origen_col IS NULL THEN 'CAB_ED origen (ORIGEN/REFERENCIA/NO_RECIBO)' END),
        (CASE WHEN @det_ed_cliente_col IS NULL THEN 'DET_ED cliente (ID_SN/CLIENTE/COD_CLIENTE)' END),
        (CASE WHEN @det_ed_debito_col IS NULL THEN 'DET_ED debito (DEBITO/DEBE)' END),
        (CASE WHEN @det_ed_credito_col IS NULL THEN 'DET_ED credito (CREDITO/HABER)' END),
        (CASE WHEN @fact_doc_col IS NULL THEN 'CAB_FACTURA documento (ID_DOC/NO_DOC/DOCUMENTO/FACTURA)' END),
        (CASE WHEN @fact_cliente_col IS NULL THEN 'CAB_FACTURA cliente (ID_SN/CLIENTE/COD_CLIENTE)' END),
        (CASE WHEN @fact_total_col IS NULL THEN 'CAB_FACTURA total (TOTAL_DOC/MONTO/IMPORTE)' END),
        (CASE WHEN @rec_id_col IS NULL THEN 'CAB_RECIBO_INGRESO clave (ID_RECIBO/ID_DOC/NO_RECIBO/NO_DOC)' END),
        (CASE WHEN @rec_no_col IS NULL THEN 'CAB_RECIBO_INGRESO numero (NO_RECIBO/NO_DOC/ID_RECIBO/ID_DOC)' END),
        (CASE WHEN @det_rec_id_col IS NULL THEN 'DET_RECIBO_INGRESO recibo (ID_RECIBO/NO_RECIBO/ID_DOC)' END),
        (CASE WHEN @det_rec_doc_col IS NULL THEN 'DET_RECIBO_INGRESO factura (NO_DOC/ID_DOC/DOCUMENTO/ID_DOC_FACTURA/FACTURA)' END),
        (CASE WHEN @det_rec_pago_col IS NULL THEN 'DET_RECIBO_INGRESO pago (TOTAL_PAGO/TOTAL_PAGO2/PAGO_ABONO/IMP_ABONO/IMP_PAGADO/MONTO_PAGO/ABONO/PAGO/IMPORTE)' END)
    ) missing(requisito)
    WHERE requisito IS NOT NULL;
    RAISERROR('Faltan columnas requeridas. Revisa el resultado COLUMNAS_FALTANTES.', 16, 1);
    RETURN;
END;

IF (@cab_ed_id_col IS NULL OR @det_ed_id_col IS NULL) AND (@cab_ed_no_col IS NULL OR @det_ed_no_col IS NULL)
BEGIN
    RAISERROR('No se encontro relacion entre CAB_ED y DET_ED por ID_DOC/ID_ED o NO_DOC/NO_ED.', 16, 1);
    RETURN;
END;

SET @det_ed_update_col = COALESCE(@det_ed_id_col, @det_ed_no_col);

SET @sql = N'
IF OBJECT_ID(''tempdb..#targets'') IS NOT NULL DROP TABLE #targets;
IF OBJECT_ID(''tempdb..#preview'') IS NOT NULL DROP TABLE #preview;
IF OBJECT_ID(''tempdb..#cab_preview'') IS NOT NULL DROP TABLE #cab_preview;

CREATE TABLE #targets (
    tipo_doc NVARCHAR(20) NOT NULL,
    origen NVARCHAR(255) NOT NULL,
    id_sn NVARCHAR(255) NOT NULL,
    tipo_key NVARCHAR(20) NOT NULL,
    origen_key NVARCHAR(255) NOT NULL,
    id_sn_key NVARCHAR(255) NOT NULL,
    debito_esperado DECIMAL(19, 4) NOT NULL,
    credito_esperado DECIMAL(19, 4) NOT NULL,
    monto_cab_esperado DECIMAL(19, 4) NOT NULL
);

INSERT INTO #targets (tipo_doc, origen, id_sn, tipo_key, origen_key, id_sn_key, debito_esperado, credito_esperado, monto_cab_esperado)
SELECT
    @p_fc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_doc_col) + N'))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N'))),
    @p_fc,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_doc_col) + N'))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N'))),
    SUM(CAST(ISNULL(f.' + QUOTENAME(@fact_total_col) + N', 0) AS DECIMAL(19, 4))),
    0,
    ABS(SUM(CAST(ISNULL(f.' + QUOTENAME(@fact_total_col) + N', 0) AS DECIMAL(19, 4))))
FROM ' + @cab_fact + N' f
WHERE LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_doc_col) + N'), @p_empty))) <> @p_empty
  AND LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N'), @p_empty))) <> @p_empty' +
  CASE WHEN @fact_estado_col IS NOT NULL THEN N'
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), f.' + QUOTENAME(@fact_estado_col) + N'), @p_empty)))) <> @p_cancelado' ELSE N'' END +
  CASE WHEN @fact_cancelado_col IS NOT NULL THEN N'
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(20), f.' + QUOTENAME(@fact_cancelado_col) + N'), @p_no)))) <> @p_yes' ELSE N'' END + N'
GROUP BY LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_doc_col) + N'))), LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N')));

INSERT INTO #targets (tipo_doc, origen, id_sn, tipo_key, origen_key, id_sn_key, debito_esperado, credito_esperado, monto_cab_esperado)
SELECT
    @p_ri,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), r.' + QUOTENAME(@rec_no_col) + N'))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N'))),
    @p_ri,
    LTRIM(RTRIM(CONVERT(VARCHAR(255), r.' + QUOTENAME(@rec_no_col) + N'))),
    LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N'))),
    0,
    SUM(CAST(ISNULL(dr.' + QUOTENAME(@det_rec_pago_col) + N', 0) AS DECIMAL(19, 4)) + ' +
        CASE WHEN @det_rec_desc_col IS NOT NULL THEN N'CAST(ISNULL(dr.' + QUOTENAME(@det_rec_desc_col) + N', 0) AS DECIMAL(19, 4))' ELSE N'0' END + N'),
    ABS(SUM(CAST(ISNULL(dr.' + QUOTENAME(@det_rec_pago_col) + N', 0) AS DECIMAL(19, 4)) + ' +
        CASE WHEN @det_rec_desc_col IS NOT NULL THEN N'CAST(ISNULL(dr.' + QUOTENAME(@det_rec_desc_col) + N', 0) AS DECIMAL(19, 4))' ELSE N'0' END + N'))
FROM ' + @det_rec + N' dr
INNER JOIN ' + @cab_rec + N' r
    ON (
        r.' + QUOTENAME(@rec_id_col) + N' = dr.' + QUOTENAME(@det_rec_id_col) + N'
        OR r.' + QUOTENAME(@rec_no_col) + N' = dr.' + QUOTENAME(@det_rec_id_col) + N'
    )
INNER JOIN ' + @cab_fact + N' f
    ON f.' + QUOTENAME(@fact_doc_col) + N' = dr.' + QUOTENAME(@det_rec_doc_col) + N'
WHERE LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(255), r.' + QUOTENAME(@rec_no_col) + N'), @p_empty))) <> @p_empty
  ' + CASE WHEN @rec_estado_col IS NOT NULL THEN N'AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), r.' + QUOTENAME(@rec_estado_col) + N'), @p_empty)))) <> @p_cancelado' ELSE N'' END +
  CASE WHEN @rec_cancelado_col IS NOT NULL THEN N'
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(20), r.' + QUOTENAME(@rec_cancelado_col) + N'), @p_no)))) <> @p_yes' ELSE N'' END + N'
GROUP BY LTRIM(RTRIM(CONVERT(VARCHAR(255), r.' + QUOTENAME(@rec_no_col) + N'))), LTRIM(RTRIM(CONVERT(VARCHAR(255), f.' + QUOTENAME(@fact_cliente_col) + N')));

DELETE FROM #targets
WHERE ABS(debito_esperado) <= @tolerancia
  AND ABS(credito_esperado) <= @tolerancia;

SELECT
    ' + CASE WHEN @cab_ed_id_col IS NOT NULL THEN N'c.' + QUOTENAME(@cab_ed_id_col) ELSE N'NULL' END + N' AS cab_ed_id,
    ' + CASE WHEN @cab_ed_no_col IS NOT NULL THEN N'c.' + QUOTENAME(@cab_ed_no_col) ELSE N'NULL' END + N' AS cab_ed_no,
    d.' + QUOTENAME(@det_ed_update_col) + N' AS det_ed_doc_key,
    ' + CASE WHEN @det_ed_no_col IS NOT NULL THEN N'd.' + QUOTENAME(@det_ed_no_col) ELSE N'NULL' END + N' AS det_ed_no_doc,
    ' + CASE WHEN @det_ed_line_col IS NOT NULL THEN N'd.' + QUOTENAME(@det_ed_line_col) ELSE N'NULL' END + N' AS det_ed_linea,
    c.' + QUOTENAME(@cab_ed_tipo_col) + N' AS tipo_doc_actual,
    c.' + QUOTENAME(@cab_ed_origen_col) + N' AS origen_actual,
    d.' + QUOTENAME(@det_ed_cliente_col) + N' AS id_sn_actual,
    CAST(ISNULL(d.' + QUOTENAME(@det_ed_debito_col) + N', 0) AS DECIMAL(19, 4)) AS debito_actual,
    CAST(ISNULL(d.' + QUOTENAME(@det_ed_credito_col) + N', 0) AS DECIMAL(19, 4)) AS credito_actual,
    t.debito_esperado,
    t.credito_esperado,
    t.monto_cab_esperado
INTO #preview
FROM ' + @cab_ed + N' c
INNER JOIN ' + @det_ed + N' d
    ON (' +
        CASE WHEN @cab_ed_id_col IS NOT NULL AND @det_ed_id_col IS NOT NULL
            THEN N'c.' + QUOTENAME(@cab_ed_id_col) + N' = d.' + QUOTENAME(@det_ed_id_col)
            ELSE N'1 = 0'
        END +
        CASE WHEN @cab_ed_no_col IS NOT NULL AND @det_ed_no_col IS NOT NULL
            THEN N' OR c.' + QUOTENAME(@cab_ed_no_col) + N' = d.' + QUOTENAME(@det_ed_no_col)
            ELSE N''
        END + N')
INNER JOIN #targets t
    ON t.tipo_key = UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.' + QUOTENAME(@cab_ed_tipo_col) + N'))))
   AND t.origen_key = LTRIM(RTRIM(CONVERT(VARCHAR(255), c.' + QUOTENAME(@cab_ed_origen_col) + N')))
   AND t.id_sn_key = LTRIM(RTRIM(CONVERT(VARCHAR(255), d.' + QUOTENAME(@det_ed_cliente_col) + N')))
WHERE 1 = 1' +
  CASE WHEN @cab_ed_estado_col IS NOT NULL THEN N'
  AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.' + QUOTENAME(@cab_ed_estado_col) + N'), @p_empty)))) <> @p_cancelado' ELSE N'' END + N'
  AND (
        ABS(CAST(ISNULL(d.' + QUOTENAME(@det_ed_debito_col) + N', 0) AS DECIMAL(19, 4)) - t.debito_esperado) > @tolerancia
     OR ABS(CAST(ISNULL(d.' + QUOTENAME(@det_ed_credito_col) + N', 0) AS DECIMAL(19, 4)) - t.credito_esperado) > @tolerancia
  );

SELECT ''PREVIEW_DET_ED_A_CORREGIR'' AS etapa, *
FROM #preview
ORDER BY tipo_doc_actual, origen_actual, id_sn_actual, det_ed_linea;

SELECT
    ''MOVIMIENTOS_SIN_LINEA_CXC_EN_DET_ED_NO_SE_CORRIGEN_AUTOMATICO'' AS etapa,
    t.tipo_doc,
    t.origen,
    t.id_sn,
    t.debito_esperado,
    t.credito_esperado
FROM #targets t
WHERE NOT EXISTS (
    SELECT 1
    FROM ' + @cab_ed + N' c
    INNER JOIN ' + @det_ed + N' d
        ON (' +
            CASE WHEN @cab_ed_id_col IS NOT NULL AND @det_ed_id_col IS NOT NULL
                THEN N'c.' + QUOTENAME(@cab_ed_id_col) + N' = d.' + QUOTENAME(@det_ed_id_col)
                ELSE N'1 = 0'
            END +
            CASE WHEN @cab_ed_no_col IS NOT NULL AND @det_ed_no_col IS NOT NULL
                THEN N' OR c.' + QUOTENAME(@cab_ed_no_col) + N' = d.' + QUOTENAME(@det_ed_no_col)
                ELSE N''
            END + N')
    WHERE t.tipo_key = UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), c.' + QUOTENAME(@cab_ed_tipo_col) + N'))))
      AND t.origen_key = LTRIM(RTRIM(CONVERT(VARCHAR(255), c.' + QUOTENAME(@cab_ed_origen_col) + N')))
      AND t.id_sn_key = LTRIM(RTRIM(CONVERT(VARCHAR(255), d.' + QUOTENAME(@det_ed_cliente_col) + N')))
      ' + CASE WHEN @cab_ed_estado_col IS NOT NULL THEN N'AND UPPER(LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(80), c.' + QUOTENAME(@cab_ed_estado_col) + N'), @p_empty)))) <> @p_cancelado' ELSE N'' END + N'
)
ORDER BY tipo_doc, origen, id_sn;

SELECT DISTINCT
    cab_ed_id,
    cab_ed_no,
    tipo_doc_actual,
    origen_actual,
    monto_cab_esperado
INTO #cab_preview
FROM #preview;

BEGIN TRANSACTION;

UPDATE d
SET d.' + QUOTENAME(@det_ed_debito_col) + N' = p.debito_esperado,
    d.' + QUOTENAME(@det_ed_credito_col) + N' = p.credito_esperado
FROM ' + @det_ed + N' d
INNER JOIN #preview p
   ON d.' + QUOTENAME(@det_ed_update_col) + N' = p.det_ed_doc_key
   ' + CASE WHEN @det_ed_line_col IS NOT NULL THEN N'AND d.' + QUOTENAME(@det_ed_line_col) + N' = p.det_ed_linea' ELSE N'AND d.' + QUOTENAME(@det_ed_cliente_col) + N' = p.id_sn_actual' END + N';
' +
CASE WHEN @cab_ed_total_col IS NOT NULL OR @cab_ed_abono_col IS NOT NULL OR @cab_ed_saldo_col IS NOT NULL THEN N'
UPDATE c
SET ' +
    STUFF(
        CASE WHEN @cab_ed_total_col IS NOT NULL THEN N', c.' + QUOTENAME(@cab_ed_total_col) + N' = p.monto_cab_esperado' ELSE N'' END +
        CASE WHEN @cab_ed_abono_col IS NOT NULL THEN N', c.' + QUOTENAME(@cab_ed_abono_col) + N' = CASE WHEN UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), p.tipo_doc_actual)))) = @p_ri THEN p.monto_cab_esperado ELSE 0 END' ELSE N'' END +
        CASE WHEN @cab_ed_saldo_col IS NOT NULL THEN N', c.' + QUOTENAME(@cab_ed_saldo_col) + N' = CASE WHEN UPPER(LTRIM(RTRIM(CONVERT(VARCHAR(20), p.tipo_doc_actual)))) = @p_fc THEN p.monto_cab_esperado ELSE 0 END' ELSE N'' END,
        1,
        2,
        N''
    ) + N'
FROM ' + @cab_ed + N' c
INNER JOIN #cab_preview p
    ON (' +
        CASE WHEN @cab_ed_id_col IS NOT NULL
            THEN N'c.' + QUOTENAME(@cab_ed_id_col) + N' = p.cab_ed_id'
            ELSE N'1 = 0'
        END +
        CASE WHEN @cab_ed_no_col IS NOT NULL
            THEN N' OR c.' + QUOTENAME(@cab_ed_no_col) + N' = p.cab_ed_no'
            ELSE N''
        END + N');
' ELSE N'' END + N'
SELECT
    (SELECT COUNT(*) FROM #targets) AS total_movimientos_fuente,
    (SELECT COUNT(*) FROM #preview) AS total_lineas_det_ed_corregidas,
    (SELECT COUNT(*) FROM #cab_preview) AS total_cab_ed_afectados;

IF @confirmar = 1
BEGIN
    COMMIT TRANSACTION;
    SELECT ''COMMIT realizado. Cambios guardados.'' AS resultado;
END
ELSE
BEGIN
    ROLLBACK TRANSACTION;
    SELECT ''ROLLBACK realizado. No se guardo ningun cambio. Cambia @confirmar a 1 para confirmar.'' AS resultado;
END;
';

IF @mostrar_sql = 1
BEGIN
    SELECT @sql AS SQL_GENERADO_PARA_DEPURAR;
END;

BEGIN TRY
    EXEC sys.sp_executesql
        @sql,
        N'@confirmar BIT, @tolerancia DECIMAL(19, 4), @p_empty NVARCHAR(1), @p_fc NVARCHAR(20), @p_ri NVARCHAR(20), @p_cancelado NVARCHAR(20), @p_no NVARCHAR(20), @p_yes NVARCHAR(20)',
        @confirmar = @confirmar,
        @tolerancia = @tolerancia,
        @p_empty = N'',
        @p_fc = N'FC',
        @p_ri = N'RI',
        @p_cancelado = N'CANCELADO',
        @p_no = N'N',
        @p_yes = N'Y';
END TRY
BEGIN CATCH
    DECLARE
        @error_line INT = ERROR_LINE(),
        @pos INT = 1,
        @next INT,
        @line_no INT = 1,
        @sql_len INT = LEN(@sql + CHAR(10));

    IF OBJECT_ID('tempdb..#sql_lines_debug') IS NOT NULL DROP TABLE #sql_lines_debug;
    CREATE TABLE #sql_lines_debug (
        line_no INT NOT NULL,
        sql_line NVARCHAR(MAX) NOT NULL
    );

    WHILE @pos <= @sql_len
    BEGIN
        SET @next = CHARINDEX(CHAR(10), @sql + CHAR(10), @pos);

        INSERT INTO #sql_lines_debug (line_no, sql_line)
        VALUES (
            @line_no,
            REPLACE(SUBSTRING(@sql, @pos, @next - @pos), CHAR(13), N'')
        );

        SET @pos = @next + 1;
        SET @line_no += 1;
    END;

    SELECT
        ERROR_NUMBER() AS error_number,
        @error_line AS error_line,
        ERROR_MESSAGE() AS error_message;

    SELECT
        'LINEAS_CERCA_DEL_ERROR' AS diagnostico,
        line_no,
        sql_line
    FROM #sql_lines_debug
    WHERE line_no BETWEEN @error_line - 8 AND @error_line + 8
    ORDER BY line_no;

    SELECT @sql AS SQL_GENERADO_PARA_DEPURAR;

    RETURN;
END CATCH;
