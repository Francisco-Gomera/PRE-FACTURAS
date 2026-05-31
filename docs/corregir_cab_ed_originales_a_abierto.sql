/*
    Corrige registros originales de CAB_ED que quedaron en estado Cancelado por error
    cuando se cancelo un recibo de ingreso.

    Criterio:
    - Busca CAB_ED tipo RI con estado Cancelado.
    - Agrupa por el origen del recibo (ORIGEN / REFERENCIA / NO_RECIBO).
    - Toma como original el CAB_ED cancelado mas antiguo del recibo.
    - Solo lo toma si existe un CAB_ED posterior, del mismo recibo, tambien
      Cancelado, cuyo comentario indica reverso: "(Documento Cancelado)".
    - Cambia SOLO el original de Cancelado a Abierto.

    Seguridad:
    - Por defecto NO confirma cambios: @confirmar = 0 hace ROLLBACK.
    - Revisa el resultado. Si todo esta correcto, cambia @confirmar a 1.
*/

SET NOCOUNT ON;

DECLARE @confirmar BIT = 0; -- Cambiar a 1 para hacer COMMIT.

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

SET @doc_key_col = CASE
    WHEN COL_LENGTH(@object_name, 'ID_DOC') IS NOT NULL THEN N'ID_DOC'
    WHEN COL_LENGTH(@object_name, 'ID_ED') IS NOT NULL THEN N'ID_ED'
    WHEN COL_LENGTH(@object_name, 'NO_DOC') IS NOT NULL THEN N'NO_DOC'
    WHEN COL_LENGTH(@object_name, 'NO_ED') IS NOT NULL THEN N'NO_ED'
END;

SET @doc_no_col = CASE
    WHEN COL_LENGTH(@object_name, 'NO_DOC') IS NOT NULL THEN N'NO_DOC'
    WHEN COL_LENGTH(@object_name, 'NO_ED') IS NOT NULL THEN N'NO_ED'
    WHEN COL_LENGTH(@object_name, 'ID_DOC') IS NOT NULL THEN N'ID_DOC'
    WHEN COL_LENGTH(@object_name, 'ID_ED') IS NOT NULL THEN N'ID_ED'
END;

SET @tipo_col = CASE
    WHEN COL_LENGTH(@object_name, 'TIPO_DOC') IS NOT NULL THEN N'TIPO_DOC'
    WHEN COL_LENGTH(@object_name, 'TD') IS NOT NULL THEN N'TD'
    WHEN COL_LENGTH(@object_name, 'CLASE_DOC') IS NOT NULL THEN N'CLASE_DOC'
    WHEN COL_LENGTH(@object_name, 'TIPO') IS NOT NULL THEN N'TIPO'
END;

SET @origen_col = CASE
    WHEN COL_LENGTH(@object_name, 'ORIGEN') IS NOT NULL THEN N'ORIGEN'
    WHEN COL_LENGTH(@object_name, 'REFERENCIA') IS NOT NULL THEN N'REFERENCIA'
    WHEN COL_LENGTH(@object_name, 'NO_RECIBO') IS NOT NULL THEN N'NO_RECIBO'
END;

SET @estado_col = CASE
    WHEN COL_LENGTH(@object_name, 'EST_DOC') IS NOT NULL THEN N'EST_DOC'
    WHEN COL_LENGTH(@object_name, 'ESTADO') IS NOT NULL THEN N'ESTADO'
    WHEN COL_LENGTH(@object_name, 'ESTATUS') IS NOT NULL THEN N'ESTATUS'
END;

SET @comentario_col = CASE
    WHEN COL_LENGTH(@object_name, 'COMENTARIO') IS NOT NULL THEN N'COMENTARIO'
    WHEN COL_LENGTH(@object_name, 'OBSERVACION') IS NOT NULL THEN N'OBSERVACION'
END;

SET @total_col = CASE
    WHEN COL_LENGTH(@object_name, 'TOTAL_DOC') IS NOT NULL THEN N'TOTAL_DOC'
    WHEN COL_LENGTH(@object_name, 'MONTO') IS NOT NULL THEN N'MONTO'
    WHEN COL_LENGTH(@object_name, 'IMPORTE') IS NOT NULL THEN N'IMPORTE'
END;

SET @fecha_col = CASE
    WHEN COL_LENGTH(@object_name, 'FECHA_CREACION') IS NOT NULL THEN N'FECHA_CREACION'
    WHEN COL_LENGTH(@object_name, 'FECHA_ACT') IS NOT NULL THEN N'FECHA_ACT'
    WHEN COL_LENGTH(@object_name, 'FECHA_CONT') IS NOT NULL THEN N'FECHA_CONT'
    WHEN COL_LENGTH(@object_name, 'F_CONT') IS NOT NULL THEN N'F_CONT'
    WHEN COL_LENGTH(@object_name, 'FECHA_DOC') IS NOT NULL THEN N'FECHA_DOC'
    WHEN COL_LENGTH(@object_name, 'FECHA_APLIC') IS NOT NULL THEN N'FECHA_APLIC'
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
BEGIN
    RAISERROR('Para actualizar se requiere COMENTARIO/OBSERVACION para identificar el reverso.', 16, 1);
    RETURN;
END;

SET @sql = N'
IF OBJECT_ID(''tempdb..#cab_ed_originales_a_corregir'') IS NOT NULL
    DROP TABLE #cab_ed_originales_a_corregir;

IF OBJECT_ID(''tempdb..#cab_ed_actualizados'') IS NOT NULL
    DROP TABLE #cab_ed_actualizados;

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
        UPPER(LTRIM(RTRIM(ISNULL(CAST(cab.' + QUOTENAME(@estado_col) + N' AS NVARCHAR(80)), '''')))) AS estado_norm,
        UPPER(LTRIM(RTRIM(ISNULL(CAST(cab.' + QUOTENAME(COALESCE(@tipo_col, @estado_col)) + N' AS NVARCHAR(80)), '''')))) AS tipo_norm,
        ISNULL(CAST(cab.' + QUOTENAME(@comentario_col) + N' AS NVARCHAR(MAX)), '''') AS comentario_text' +
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
        cab.' + QUOTENAME(@fecha_col) + N' AS fecha_ref'
            ELSE N',
        CAST(NULL AS DATETIME) AS fecha_ref'
        END + N'
    FROM ' + @full_table + N' AS cab
),
cancelados_ri AS (
    SELECT *
    FROM base
    WHERE estado_norm = ''CANCELADO''
      AND ' + CASE WHEN @tipo_col IS NOT NULL THEN N'tipo_norm = ''RI''' ELSE N'1 = 1' END + N'
      AND origen_text <> ''''
),
candidatos AS (
    SELECT
        original.doc_key_text,
        original.doc_no_text,
        original.doc_no_num,
        original.origen_text,
        original.' + QUOTENAME(@estado_col) + N' AS estado_antes' +
        CASE WHEN @total_col IS NOT NULL THEN N',
        original.' + QUOTENAME(@total_col) + N' AS total_original' ELSE N',
        CAST(NULL AS DECIMAL(19, 4)) AS total_original' END +
        CASE WHEN @fecha_col IS NOT NULL THEN N',
        original.' + QUOTENAME(@fecha_col) + N' AS fecha_original' ELSE N',
        CAST(NULL AS DATETIME) AS fecha_original' END + N',
        original.comentario_text AS comentario_original,
        ROW_NUMBER() OVER (
            PARTITION BY original.origen_text
            ORDER BY
                CASE WHEN original.doc_no_num IS NULL THEN 1 ELSE 0 END,
                original.doc_no_num,
                original.doc_no_text
        ) AS rn
    FROM cancelados_ri AS original
    WHERE EXISTS (
        SELECT 1
        FROM cancelados_ri AS reverso
        WHERE reverso.origen_text = original.origen_text
          AND reverso.doc_key_text <> original.doc_key_text
          AND reverso.comentario_text LIKE ''%(Documento Cancelado)%''
          AND (
                (reverso.doc_no_num IS NOT NULL AND original.doc_no_num IS NOT NULL AND reverso.doc_no_num > original.doc_no_num)
                OR (reverso.doc_no_num IS NULL OR original.doc_no_num IS NULL)
          )' +
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
)
SELECT
    doc_key_text,
    doc_no_text,
    doc_no_num,
    origen_text,
    estado_antes,
    total_original,
    fecha_original,
    comentario_original
INTO #cab_ed_originales_a_corregir
FROM candidatos
WHERE rn = 1;

SELECT
    ''ANTES DE ACTUALIZAR'' AS etapa,
    *
FROM #cab_ed_originales_a_corregir
ORDER BY
    CASE WHEN doc_no_num IS NULL THEN 1 ELSE 0 END,
    doc_no_num,
    origen_text,
    doc_no_text;

CREATE TABLE #cab_ed_actualizados (
    doc_key_text NVARCHAR(255) NULL,
    doc_no_text NVARCHAR(255) NULL,
    origen_text NVARCHAR(255) NULL,
    estado_antes NVARCHAR(80) NULL,
    estado_despues NVARCHAR(80) NULL
);

BEGIN TRANSACTION;

UPDATE cab
SET cab.' + QUOTENAME(@estado_col) + N' = ''Abierto''
OUTPUT
    CAST(inserted.' + QUOTENAME(COALESCE(@doc_key_col, @doc_no_col)) + N' AS NVARCHAR(255)),
    CAST(inserted.' + QUOTENAME(COALESCE(@doc_no_col, @doc_key_col)) + N' AS NVARCHAR(255)),
    CAST(inserted.' + QUOTENAME(@origen_col) + N' AS NVARCHAR(255)),
    CAST(deleted.' + QUOTENAME(@estado_col) + N' AS NVARCHAR(80)),
    CAST(inserted.' + QUOTENAME(@estado_col) + N' AS NVARCHAR(80))
INTO #cab_ed_actualizados (
    doc_key_text,
    doc_no_text,
    origen_text,
    estado_antes,
    estado_despues
)
FROM ' + @full_table + N' AS cab
INNER JOIN #cab_ed_originales_a_corregir AS c
    ON CAST(cab.' + QUOTENAME(COALESCE(@doc_key_col, @doc_no_col)) + N' AS NVARCHAR(255)) = c.doc_key_text
WHERE UPPER(LTRIM(RTRIM(ISNULL(CAST(cab.' + QUOTENAME(@estado_col) + N' AS NVARCHAR(80)), '''')))) = ''CANCELADO'';

SELECT
    ''ACTUALIZADOS EN TRANSACCION'' AS etapa,
    *
FROM #cab_ed_actualizados
ORDER BY
    origen_text,
    doc_no_text;

SELECT COUNT(*) AS total_registros_actualizados
FROM #cab_ed_actualizados;

IF @confirmar = 1
BEGIN
    COMMIT TRANSACTION;
    SELECT ''COMMIT realizado. Los originales quedaron en estado Abierto.'' AS resultado;
END
ELSE
BEGIN
    ROLLBACK TRANSACTION;
    SELECT ''ROLLBACK realizado. No se guardo ningun cambio. Cambia @confirmar a 1 para confirmar.'' AS resultado;
END;
';

EXEC sys.sp_executesql
    @sql,
    N'@confirmar BIT',
    @confirmar = @confirmar;
