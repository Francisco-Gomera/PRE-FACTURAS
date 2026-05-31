/*
    Identifica registros de CAB_ED que quedaron en estado Cancelado por error
    cuando se cancelo un recibo de ingreso.

    Criterio:
    - Busca CAB_ED tipo RI con estado Cancelado.
    - Agrupa por el origen del recibo (ORIGEN / REFERENCIA / NO_RECIBO).
    - Marca como sospechoso el CAB_ED cancelado que tiene otro CAB_ED posterior,
      del mismo recibo, tambien Cancelado, cuyo comentario indica reverso:
      "(Documento Cancelado)".

    Este script NO actualiza datos.
*/

SET NOCOUNT ON;

DECLARE @schema SYSNAME = N'dbo';
DECLARE @table SYSNAME = N'CAB_ED';
DECLARE @object_name NVARCHAR(300) = @schema + N'.' + @table;
DECLARE @full_table NVARCHAR(300) = QUOTENAME(@schema) + N'.' + QUOTENAME(@table);

DECLARE
    @doc_key_col SYSNAME,
    @doc_no_col SYSNAME,
    @tipo_col SYSNAME,
    @origen_col SYSNAME,
    @estado_col SYSNAME,
    @comentario_col SYSNAME,
    @total_col SYSNAME,
    @fecha_col SYSNAME,
    @sql NVARCHAR(MAX);

IF OBJECT_ID(@object_name, N'U') IS NULL
BEGIN
    RAISERROR('No existe la tabla indicada en @schema/@table.', 16, 1);
    RETURN;
END;

SELECT @doc_key_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'ID_DOC', N'ID_ED', N'NO_DOC', N'NO_ED')
ORDER BY CASE name
    WHEN N'ID_DOC' THEN 1
    WHEN N'ID_ED' THEN 2
    WHEN N'NO_DOC' THEN 3
    WHEN N'NO_ED' THEN 4
END;

SELECT @doc_no_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'NO_DOC', N'NO_ED', N'ID_DOC', N'ID_ED')
ORDER BY CASE name
    WHEN N'NO_DOC' THEN 1
    WHEN N'NO_ED' THEN 2
    WHEN N'ID_DOC' THEN 3
    WHEN N'ID_ED' THEN 4
END;

SELECT @tipo_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'TIPO_DOC', N'TD', N'CLASE_DOC', N'TIPO')
ORDER BY CASE name
    WHEN N'TIPO_DOC' THEN 1
    WHEN N'TD' THEN 2
    WHEN N'CLASE_DOC' THEN 3
    WHEN N'TIPO' THEN 4
END;

SELECT @origen_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'ORIGEN', N'REFERENCIA', N'NO_RECIBO')
ORDER BY CASE name
    WHEN N'ORIGEN' THEN 1
    WHEN N'REFERENCIA' THEN 2
    WHEN N'NO_RECIBO' THEN 3
END;

SELECT @estado_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'EST_DOC', N'ESTADO', N'ESTATUS')
ORDER BY CASE name
    WHEN N'EST_DOC' THEN 1
    WHEN N'ESTADO' THEN 2
    WHEN N'ESTATUS' THEN 3
END;

SELECT @comentario_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'COMENTARIO', N'OBSERVACION')
ORDER BY CASE name
    WHEN N'COMENTARIO' THEN 1
    WHEN N'OBSERVACION' THEN 2
END;

SELECT @total_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'TOTAL_DOC', N'MONTO', N'IMPORTE')
ORDER BY CASE name
    WHEN N'TOTAL_DOC' THEN 1
    WHEN N'MONTO' THEN 2
    WHEN N'IMPORTE' THEN 3
END;

SELECT @fecha_col = name
FROM sys.columns
WHERE object_id = OBJECT_ID(@object_name)
  AND name IN (N'FECHA_CREACION', N'FECHA_ACT', N'FECHA_CONT', N'F_CONT', N'FECHA_DOC', N'FECHA_APLIC')
ORDER BY CASE name
    WHEN N'FECHA_CREACION' THEN 1
    WHEN N'FECHA_ACT' THEN 2
    WHEN N'FECHA_CONT' THEN 3
    WHEN N'F_CONT' THEN 4
    WHEN N'FECHA_DOC' THEN 5
    WHEN N'FECHA_APLIC' THEN 6
END;

IF @doc_key_col IS NULL AND @doc_no_col IS NULL
BEGIN
    RAISERROR('No se encontro columna de documento en CAB_ED (ID_DOC/ID_ED/NO_DOC/NO_ED).', 16, 1);
    RETURN;
END;

IF @origen_col IS NULL
BEGIN
    RAISERROR('No se encontro columna de origen en CAB_ED (ORIGEN/REFERENCIA/NO_RECIBO).', 16, 1);
    RETURN;
END;

IF @estado_col IS NULL
BEGIN
    RAISERROR('No se encontro columna de estado en CAB_ED (EST_DOC/ESTADO/ESTATUS).', 16, 1);
    RETURN;
END;

IF @comentario_col IS NULL
    PRINT 'Aviso: no existe COMENTARIO/OBSERVACION; se usara solo duplicidad por origen y estado.';

SET @sql = N'
IF OBJECT_ID(''tempdb..#cab_ed_cancelados_erroneos'') IS NOT NULL
    DROP TABLE #cab_ed_cancelados_erroneos;

;WITH base AS (
    SELECT
        cab.*,
        CAST(cab.' + QUOTENAME(COALESCE(@doc_key_col, @doc_no_col)) + N' AS NVARCHAR(255)) AS doc_key_text,
        CAST(cab.' + QUOTENAME(COALESCE(@doc_no_col, @doc_key_col)) + N' AS NVARCHAR(255)) AS doc_no_text,
        CASE
            WHEN ISNUMERIC(REPLACE(LTRIM(RTRIM(CAST(cab.' + QUOTENAME(COALESCE(@doc_no_col, @doc_key_col)) + N' AS NVARCHAR(255)))), '','', '''')) = 1
            THEN CAST(REPLACE(LTRIM(RTRIM(CAST(cab.' + QUOTENAME(COALESCE(@doc_no_col, @doc_key_col)) + N' AS NVARCHAR(255)))), '','', '''') AS DECIMAL(38, 0))
            ELSE NULL
        END AS doc_no_num,
        LTRIM(RTRIM(CAST(cab.' + QUOTENAME(@origen_col) + N' AS NVARCHAR(255)))) AS origen_text,
        UPPER(LTRIM(RTRIM(ISNULL(CAST(cab.' + QUOTENAME(@estado_col) + N' AS NVARCHAR(80)), '''')))) AS estado_norm' +
        CASE WHEN @tipo_col IS NOT NULL
            THEN N',
        UPPER(LTRIM(RTRIM(ISNULL(CAST(cab.' + QUOTENAME(@tipo_col) + N' AS NVARCHAR(80)), '''')))) AS tipo_norm'
            ELSE N',
        CAST(''RI'' AS NVARCHAR(80)) AS tipo_norm'
        END +
        CASE WHEN @comentario_col IS NOT NULL
            THEN N',
        CAST(ISNULL(cab.' + QUOTENAME(@comentario_col) + N', '''') AS NVARCHAR(MAX)) AS comentario_text'
            ELSE N',
        CAST('''' AS NVARCHAR(MAX)) AS comentario_text'
        END +
        CASE WHEN @total_col IS NOT NULL
            THEN N',
        CASE
            WHEN ISNUMERIC(REPLACE(LTRIM(RTRIM(CAST(cab.' + QUOTENAME(@total_col) + N' AS NVARCHAR(255)))), '','', '''')) = 1
            THEN CAST(REPLACE(LTRIM(RTRIM(CAST(cab.' + QUOTENAME(@total_col) + N' AS NVARCHAR(255)))), '','', '''') AS DECIMAL(19, 4))
            ELSE NULL
        END AS total_num'
            ELSE N',
        CAST(NULL AS DECIMAL(19, 4)) AS total_num'
        END +
        CASE WHEN @fecha_col IS NOT NULL
            THEN N',
        CONVERT(DATETIME, cab.' + QUOTENAME(@fecha_col) + N') AS fecha_ref'
            ELSE N',
        CAST(NULL AS DATETIME) AS fecha_ref'
        END + N'
    FROM ' + @full_table + N' AS cab
),
cancelados_ri AS (
    SELECT *
    FROM base
    WHERE estado_norm = ''CANCELADO''
      AND tipo_norm = ''RI''
      AND origen_text <> ''''
),
pares AS (
    SELECT
        original.origen_text AS origen_recibo,
        original.doc_key_text AS cab_ed_original_id,
        original.doc_no_text AS cab_ed_original_no,
        original.' + QUOTENAME(@estado_col) + N' AS estado_actual_original' +
        CASE WHEN @total_col IS NOT NULL THEN N',
        original.' + QUOTENAME(@total_col) + N' AS total_original' ELSE N',
        CAST(NULL AS DECIMAL(19, 4)) AS total_original' END +
        CASE WHEN @fecha_col IS NOT NULL THEN N',
        original.' + QUOTENAME(@fecha_col) + N' AS fecha_original' ELSE N',
        CAST(NULL AS DATETIME) AS fecha_original' END +
        CASE WHEN @comentario_col IS NOT NULL THEN N',
        original.' + QUOTENAME(@comentario_col) + N' AS comentario_original' ELSE N',
        CAST(NULL AS NVARCHAR(MAX)) AS comentario_original' END + N',
        reverso.doc_key_text AS cab_ed_reverso_id,
        reverso.doc_no_text AS cab_ed_reverso_no,
        reverso.' + QUOTENAME(@estado_col) + N' AS estado_reverso' +
        CASE WHEN @total_col IS NOT NULL THEN N',
        reverso.' + QUOTENAME(@total_col) + N' AS total_reverso' ELSE N',
        CAST(NULL AS DECIMAL(19, 4)) AS total_reverso' END +
        CASE WHEN @fecha_col IS NOT NULL THEN N',
        reverso.' + QUOTENAME(@fecha_col) + N' AS fecha_reverso' ELSE N',
        CAST(NULL AS DATETIME) AS fecha_reverso' END +
        CASE WHEN @comentario_col IS NOT NULL THEN N',
        reverso.' + QUOTENAME(@comentario_col) + N' AS comentario_reverso' ELSE N',
        CAST(NULL AS NVARCHAR(MAX)) AS comentario_reverso' END + N',
        ''Original cancelado con reverso cancelado posterior del mismo recibo'' AS criterio
    FROM cancelados_ri AS original
    INNER JOIN cancelados_ri AS reverso
        ON reverso.origen_text = original.origen_text
       AND reverso.doc_key_text <> original.doc_key_text
       AND (
            (reverso.doc_no_num IS NOT NULL AND original.doc_no_num IS NOT NULL AND reverso.doc_no_num > original.doc_no_num)
            OR (reverso.doc_no_num IS NULL OR original.doc_no_num IS NULL)
       )' +
       CASE WHEN @comentario_col IS NOT NULL
            THEN N'
       AND reverso.comentario_text LIKE ''%(Documento Cancelado)%'''
            ELSE N''
       END +
       CASE WHEN @total_col IS NOT NULL
            THEN N'
       AND (
            original.total_num IS NULL
            OR reverso.total_num IS NULL
            OR ABS(original.total_num - reverso.total_num) <= 0.01
       )'
            ELSE N''
       END + N'
)
SELECT *
INTO #cab_ed_cancelados_erroneos
FROM pares;

SELECT *
FROM #cab_ed_cancelados_erroneos
ORDER BY
    CASE
        WHEN ISNUMERIC(REPLACE(LTRIM(RTRIM(CAST(cab_ed_original_no AS NVARCHAR(255)))), '','', '''')) = 1
        THEN CAST(REPLACE(LTRIM(RTRIM(CAST(cab_ed_original_no AS NVARCHAR(255)))), '','', '''') AS DECIMAL(38, 0))
        ELSE NULL
    END,
    origen_recibo,
    cab_ed_original_no;

SELECT
    COUNT(DISTINCT cab_ed_original_id) AS total_cab_ed_originales_sospechosos,
    COUNT(*) AS total_pares_original_reverso
FROM #cab_ed_cancelados_erroneos;
';

EXEC sys.sp_executesql @sql;
