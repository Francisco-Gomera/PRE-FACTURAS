/*
    Diagnostica clientes con discrepancia entre:

    1) Balance CxC segun asientos abiertos en CAB_ED/DET_ED:
       SUM(DEBITOS) - SUM(CREDITOS)

    2) Balance real pendiente segun CAB_FACTURA:
       SUM(SALDO) de facturas abiertas.
       Si SALDO esta en 0 pero TOTAL_DOC - ABONO da pendiente, usa ese valor.

    Este script NO actualiza datos.

    Ajustes utiles:
    - @solo_discrepancias = 1: muestra solo diferencias mayores a @tolerancia.
    - @solo_con_movimiento = 1: oculta clientes sin balance ni facturas.
*/

SET NOCOUNT ON;

DECLARE @schema SYSNAME = N'dbo';
DECLARE @tolerancia DECIMAL(19, 4) = 0.01;
DECLARE @solo_discrepancias BIT = 1;
DECLARE @solo_con_movimiento BIT = 1;

DECLARE
    @cab_ed_obj NVARCHAR(300),
    @det_ed_obj NVARCHAR(300),
    @cab_fact_obj NVARCHAR(300),
    @maestro_obj NVARCHAR(300),
    @cab_ed_full NVARCHAR(300),
    @det_ed_full NVARCHAR(300),
    @cab_fact_full NVARCHAR(300),
    @maestro_full NVARCHAR(300),
    @cab_ed_id_col SYSNAME,
    @cab_ed_no_col SYSNAME,
    @cab_ed_estado_col SYSNAME,
    @det_ed_id_col SYSNAME,
    @det_ed_no_col SYSNAME,
    @det_ed_cliente_col SYSNAME,
    @det_ed_debito_col SYSNAME,
    @det_ed_credito_col SYSNAME,
    @fact_cliente_col SYSNAME,
    @fact_doc_col SYSNAME,
    @fact_estado_col SYSNAME,
    @fact_total_col SYSNAME,
    @fact_saldo_col SYSNAME,
    @fact_abono_col SYSNAME,
    @sn_cliente_col SYSNAME,
    @sn_nombre_col SYSNAME,
    @sn_rnc_col SYSNAME,
    @sql NVARCHAR(MAX);

SET @cab_ed_obj = @schema + N'.CAB_ED';
SET @det_ed_obj = @schema + N'.DET_ED';
SET @cab_fact_obj = @schema + N'.CAB_FACTURA';
SET @maestro_obj = @schema + N'.MAESTRO_SN';

SET @cab_ed_full = QUOTENAME(@schema) + N'.[CAB_ED]';
SET @det_ed_full = QUOTENAME(@schema) + N'.[DET_ED]';
SET @cab_fact_full = QUOTENAME(@schema) + N'.[CAB_FACTURA]';
SET @maestro_full = QUOTENAME(@schema) + N'.[MAESTRO_SN]';

IF OBJECT_ID(@cab_ed_obj, N'U') IS NULL
BEGIN
    RAISERROR('No existe CAB_ED.', 16, 1);
    RETURN;
END;

IF OBJECT_ID(@det_ed_obj, N'U') IS NULL
BEGIN
    RAISERROR('No existe DET_ED.', 16, 1);
    RETURN;
END;

IF OBJECT_ID(@cab_fact_obj, N'U') IS NULL
BEGIN
    RAISERROR('No existe CAB_FACTURA.', 16, 1);
    RETURN;
END;

SET @cab_ed_id_col = CASE
    WHEN COL_LENGTH(@cab_ed_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC'
    WHEN COL_LENGTH(@cab_ed_obj, 'ID_ED') IS NOT NULL THEN N'ID_ED'
END;

SET @cab_ed_no_col = CASE
    WHEN COL_LENGTH(@cab_ed_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC'
    WHEN COL_LENGTH(@cab_ed_obj, 'NO_ED') IS NOT NULL THEN N'NO_ED'
END;

SET @cab_ed_estado_col = CASE
    WHEN COL_LENGTH(@cab_ed_obj, 'ESTATUS') IS NOT NULL THEN N'ESTATUS'
    WHEN COL_LENGTH(@cab_ed_obj, 'EST_DOC') IS NOT NULL THEN N'EST_DOC'
    WHEN COL_LENGTH(@cab_ed_obj, 'ESTADO') IS NOT NULL THEN N'ESTADO'
END;

SET @det_ed_id_col = CASE
    WHEN COL_LENGTH(@det_ed_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC'
    WHEN COL_LENGTH(@det_ed_obj, 'ID_ED') IS NOT NULL THEN N'ID_ED'
END;

SET @det_ed_no_col = CASE
    WHEN COL_LENGTH(@det_ed_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC'
    WHEN COL_LENGTH(@det_ed_obj, 'NO_ED') IS NOT NULL THEN N'NO_ED'
END;

SET @det_ed_cliente_col = CASE
    WHEN COL_LENGTH(@det_ed_obj, 'ID_SN') IS NOT NULL THEN N'ID_SN'
    WHEN COL_LENGTH(@det_ed_obj, 'CLIENTE') IS NOT NULL THEN N'CLIENTE'
    WHEN COL_LENGTH(@det_ed_obj, 'COD_CLIENTE') IS NOT NULL THEN N'COD_CLIENTE'
END;

SET @det_ed_debito_col = CASE
    WHEN COL_LENGTH(@det_ed_obj, 'DEBITO') IS NOT NULL THEN N'DEBITO'
    WHEN COL_LENGTH(@det_ed_obj, 'DEBE') IS NOT NULL THEN N'DEBE'
END;

SET @det_ed_credito_col = CASE
    WHEN COL_LENGTH(@det_ed_obj, 'CREDITO') IS NOT NULL THEN N'CREDITO'
    WHEN COL_LENGTH(@det_ed_obj, 'HABER') IS NOT NULL THEN N'HABER'
END;

SET @fact_cliente_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'ID_SN') IS NOT NULL THEN N'ID_SN'
    WHEN COL_LENGTH(@cab_fact_obj, 'CLIENTE') IS NOT NULL THEN N'CLIENTE'
    WHEN COL_LENGTH(@cab_fact_obj, 'COD_CLIENTE') IS NOT NULL THEN N'COD_CLIENTE'
END;

SET @fact_doc_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'ID_DOC') IS NOT NULL THEN N'ID_DOC'
    WHEN COL_LENGTH(@cab_fact_obj, 'NO_DOC') IS NOT NULL THEN N'NO_DOC'
    WHEN COL_LENGTH(@cab_fact_obj, 'FACTURA') IS NOT NULL THEN N'FACTURA'
END;

SET @fact_estado_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'EST_DOC') IS NOT NULL THEN N'EST_DOC'
    WHEN COL_LENGTH(@cab_fact_obj, 'ESTATUS') IS NOT NULL THEN N'ESTATUS'
    WHEN COL_LENGTH(@cab_fact_obj, 'ESTADO') IS NOT NULL THEN N'ESTADO'
END;

SET @fact_total_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'TOTAL_DOC') IS NOT NULL THEN N'TOTAL_DOC'
    WHEN COL_LENGTH(@cab_fact_obj, 'MONTO') IS NOT NULL THEN N'MONTO'
    WHEN COL_LENGTH(@cab_fact_obj, 'IMPORTE') IS NOT NULL THEN N'IMPORTE'
END;

SET @fact_saldo_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'SALDO') IS NOT NULL THEN N'SALDO'
    WHEN COL_LENGTH(@cab_fact_obj, 'BALANCE') IS NOT NULL THEN N'BALANCE'
    WHEN COL_LENGTH(@cab_fact_obj, 'SALDO_INSOLUTO') IS NOT NULL THEN N'SALDO_INSOLUTO'
END;

SET @fact_abono_col = CASE
    WHEN COL_LENGTH(@cab_fact_obj, 'ABONO') IS NOT NULL THEN N'ABONO'
    WHEN COL_LENGTH(@cab_fact_obj, 'PAGADO') IS NOT NULL THEN N'PAGADO'
END;

IF OBJECT_ID(@maestro_obj, N'U') IS NOT NULL
BEGIN
    SET @sn_cliente_col = CASE
        WHEN COL_LENGTH(@maestro_obj, 'ID_SN') IS NOT NULL THEN N'ID_SN'
        WHEN COL_LENGTH(@maestro_obj, 'CLIENTE') IS NOT NULL THEN N'CLIENTE'
        WHEN COL_LENGTH(@maestro_obj, 'COD_CLIENTE') IS NOT NULL THEN N'COD_CLIENTE'
    END;

    SET @sn_nombre_col = CASE
        WHEN COL_LENGTH(@maestro_obj, 'NOM_SOCIO') IS NOT NULL THEN N'NOM_SOCIO'
        WHEN COL_LENGTH(@maestro_obj, 'NOM_SN') IS NOT NULL THEN N'NOM_SN'
        WHEN COL_LENGTH(@maestro_obj, 'NOMBRE') IS NOT NULL THEN N'NOMBRE'
        WHEN COL_LENGTH(@maestro_obj, 'NOM_CLIENTE') IS NOT NULL THEN N'NOM_CLIENTE'
    END;

    SET @sn_rnc_col = CASE
        WHEN COL_LENGTH(@maestro_obj, 'RNC_CED') IS NOT NULL THEN N'RNC_CED'
        WHEN COL_LENGTH(@maestro_obj, 'RNC') IS NOT NULL THEN N'RNC'
        WHEN COL_LENGTH(@maestro_obj, 'CEDULA') IS NOT NULL THEN N'CEDULA'
    END;
END;

IF @cab_ed_estado_col IS NULL OR @det_ed_cliente_col IS NULL OR @det_ed_debito_col IS NULL OR @det_ed_credito_col IS NULL
BEGIN
    RAISERROR('Faltan columnas necesarias en CAB_ED/DET_ED.', 16, 1);
    RETURN;
END;

IF (@cab_ed_id_col IS NULL OR @det_ed_id_col IS NULL) AND (@cab_ed_no_col IS NULL OR @det_ed_no_col IS NULL)
BEGIN
    RAISERROR('No se encontro relacion entre CAB_ED y DET_ED por ID_DOC/ID_ED o NO_DOC/NO_ED.', 16, 1);
    RETURN;
END;

IF @fact_cliente_col IS NULL OR @fact_estado_col IS NULL OR @fact_total_col IS NULL OR @fact_saldo_col IS NULL
BEGIN
    RAISERROR('Faltan columnas necesarias en CAB_FACTURA.', 16, 1);
    RETURN;
END;

SET @sql = N'
;WITH ed_balance AS (
    SELECT
        LTRIM(RTRIM(CAST(d.' + QUOTENAME(@det_ed_cliente_col) + N' AS NVARCHAR(255)))) AS id_sn,
        SUM(ISNULL(CAST(d.' + QUOTENAME(@det_ed_debito_col) + N' AS DECIMAL(19, 4)), 0)) AS total_debitos_ed,
        SUM(ISNULL(CAST(d.' + QUOTENAME(@det_ed_credito_col) + N' AS DECIMAL(19, 4)), 0)) AS total_creditos_ed,
        SUM(ISNULL(CAST(d.' + QUOTENAME(@det_ed_debito_col) + N' AS DECIMAL(19, 4)), 0))
            - SUM(ISNULL(CAST(d.' + QUOTENAME(@det_ed_credito_col) + N' AS DECIMAL(19, 4)), 0)) AS balance_ed,
        COUNT(*) AS lineas_det_ed
    FROM ' + @det_ed_full + N' d
    WHERE LTRIM(RTRIM(ISNULL(CAST(d.' + QUOTENAME(@det_ed_cliente_col) + N' AS NVARCHAR(255)), ''''))) <> ''''
      AND EXISTS (
          SELECT 1
          FROM ' + @cab_ed_full + N' c
          WHERE UPPER(LTRIM(RTRIM(ISNULL(CAST(c.' + QUOTENAME(@cab_ed_estado_col) + N' AS NVARCHAR(80)), '''')))) = ''ABIERTO''
            AND (' +
                CASE WHEN @cab_ed_id_col IS NOT NULL AND @det_ed_id_col IS NOT NULL
                    THEN N'CAST(c.' + QUOTENAME(@cab_ed_id_col) + N' AS NVARCHAR(255)) = CAST(d.' + QUOTENAME(@det_ed_id_col) + N' AS NVARCHAR(255))'
                    ELSE N'1 = 0'
                END +
                CASE WHEN @cab_ed_no_col IS NOT NULL AND @det_ed_no_col IS NOT NULL
                    THEN N' OR CAST(c.' + QUOTENAME(@cab_ed_no_col) + N' AS NVARCHAR(255)) = CAST(d.' + QUOTENAME(@det_ed_no_col) + N' AS NVARCHAR(255))'
                    ELSE N''
                END + N'
            )
      )
    GROUP BY LTRIM(RTRIM(CAST(d.' + QUOTENAME(@det_ed_cliente_col) + N' AS NVARCHAR(255))))
),
facturas_pendientes AS (
    SELECT
        LTRIM(RTRIM(CAST(f.' + QUOTENAME(@fact_cliente_col) + N' AS NVARCHAR(255)))) AS id_sn,
        COUNT(*) AS facturas_abiertas,
        SUM(ISNULL(CAST(f.' + QUOTENAME(@fact_total_col) + N' AS DECIMAL(19, 4)), 0)) AS total_facturas_abiertas,
        SUM(
            CASE
                WHEN ISNULL(CAST(f.' + QUOTENAME(@fact_saldo_col) + N' AS DECIMAL(19, 4)), 0) > 0.01
                    THEN ISNULL(CAST(f.' + QUOTENAME(@fact_saldo_col) + N' AS DECIMAL(19, 4)), 0)
                ELSE
                    CASE
                        WHEN ISNULL(CAST(f.' + QUOTENAME(@fact_total_col) + N' AS DECIMAL(19, 4)), 0)
                             - ' + CASE WHEN @fact_abono_col IS NOT NULL
                                    THEN N'ISNULL(CAST(f.' + QUOTENAME(@fact_abono_col) + N' AS DECIMAL(19, 4)), 0)'
                                    ELSE N'0'
                                END + N' > 0.01
                        THEN ISNULL(CAST(f.' + QUOTENAME(@fact_total_col) + N' AS DECIMAL(19, 4)), 0)
                             - ' + CASE WHEN @fact_abono_col IS NOT NULL
                                    THEN N'ISNULL(CAST(f.' + QUOTENAME(@fact_abono_col) + N' AS DECIMAL(19, 4)), 0)'
                                    ELSE N'0'
                                END + N'
                        ELSE 0
                    END
            END
        ) AS saldo_facturas_pendientes
    FROM ' + @cab_fact_full + N' f
    WHERE LTRIM(RTRIM(ISNULL(CAST(f.' + QUOTENAME(@fact_cliente_col) + N' AS NVARCHAR(255)), ''''))) <> ''''
      AND UPPER(LTRIM(RTRIM(ISNULL(CAST(f.' + QUOTENAME(@fact_estado_col) + N' AS NVARCHAR(80)), '''')))) = ''ABIERTO''
    GROUP BY LTRIM(RTRIM(CAST(f.' + QUOTENAME(@fact_cliente_col) + N' AS NVARCHAR(255))))
),
clientes AS (
    SELECT id_sn FROM ed_balance
    UNION
    SELECT id_sn FROM facturas_pendientes
)
SELECT
    clientes.id_sn' +
    CASE WHEN @sn_cliente_col IS NOT NULL AND @sn_nombre_col IS NOT NULL
        THEN N',
    CAST(sn.' + QUOTENAME(@sn_nombre_col) + N' AS NVARCHAR(255)) AS nombre_cliente'
        ELSE N',
    CAST(NULL AS NVARCHAR(255)) AS nombre_cliente'
    END +
    CASE WHEN @sn_cliente_col IS NOT NULL AND @sn_rnc_col IS NOT NULL
        THEN N',
    CAST(sn.' + QUOTENAME(@sn_rnc_col) + N' AS NVARCHAR(80)) AS rnc_ced'
        ELSE N',
    CAST(NULL AS NVARCHAR(80)) AS rnc_ced'
    END + N',
    ISNULL(ed.total_debitos_ed, 0) AS total_debitos_ed,
    ISNULL(ed.total_creditos_ed, 0) AS total_creditos_ed,
    ISNULL(ed.balance_ed, 0) AS balance_segun_recibos_ed,
    ISNULL(fp.saldo_facturas_pendientes, 0) AS saldo_segun_facturas_pendientes,
    ISNULL(ed.balance_ed, 0) - ISNULL(fp.saldo_facturas_pendientes, 0) AS diferencia,
    ABS(ISNULL(ed.balance_ed, 0) - ISNULL(fp.saldo_facturas_pendientes, 0)) AS diferencia_abs,
    ISNULL(fp.facturas_abiertas, 0) AS facturas_abiertas,
    ISNULL(fp.total_facturas_abiertas, 0) AS total_facturas_abiertas,
    ISNULL(ed.lineas_det_ed, 0) AS lineas_det_ed,
    CASE
        WHEN ISNULL(ed.balance_ed, 0) > ISNULL(fp.saldo_facturas_pendientes, 0) THEN ''ED_MAYOR_QUE_FACTURAS''
        WHEN ISNULL(ed.balance_ed, 0) < ISNULL(fp.saldo_facturas_pendientes, 0) THEN ''FACTURAS_MAYOR_QUE_ED''
        ELSE ''IGUAL''
    END AS tipo_diferencia
FROM clientes
LEFT JOIN ed_balance ed ON ed.id_sn = clientes.id_sn
LEFT JOIN facturas_pendientes fp ON fp.id_sn = clientes.id_sn' +
    CASE WHEN @sn_cliente_col IS NOT NULL
        THEN N'
LEFT JOIN ' + @maestro_full + N' sn ON LTRIM(RTRIM(CAST(sn.' + QUOTENAME(@sn_cliente_col) + N' AS NVARCHAR(255)))) = clientes.id_sn'
        ELSE N''
    END + N'
WHERE (@solo_discrepancias = 0 OR ABS(ISNULL(ed.balance_ed, 0) - ISNULL(fp.saldo_facturas_pendientes, 0)) > @tolerancia)
  AND (@solo_con_movimiento = 0 OR ISNULL(ed.balance_ed, 0) <> 0 OR ISNULL(fp.saldo_facturas_pendientes, 0) <> 0)
ORDER BY
    ABS(ISNULL(ed.balance_ed, 0) - ISNULL(fp.saldo_facturas_pendientes, 0)) DESC,
    clientes.id_sn;
';

EXEC sys.sp_executesql
    @sql,
    N'@tolerancia DECIMAL(19, 4), @solo_discrepancias BIT, @solo_con_movimiento BIT',
    @tolerancia = @tolerancia,
    @solo_discrepancias = @solo_discrepancias,
    @solo_con_movimiento = @solo_con_movimiento;
