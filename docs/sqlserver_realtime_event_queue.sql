/*
    Cola de eventos para que Django/Channels emita websockets
    aun cuando otro sistema escriba directamente en la misma base de datos.

    Flujo:
    1. Los triggers insertan eventos en WS_EVENT_QUEUE.
    2. Django ejecuta: python manage.py consume_realtime_db_events
    3. Ese worker consume la cola y hace group_send por websocket.
*/

IF OBJECT_ID('dbo.WS_EVENT_QUEUE', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.WS_EVENT_QUEUE (
        ID_EVENTO BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        CANAL NVARCHAR(60) NOT NULL,
        TIPO_EVENTO NVARCHAR(60) NOT NULL,
        DOCUMENT_ID NVARCHAR(80) NULL,
        ESTADO_DOC NVARCHAR(40) NULL,
        RAZON NVARCHAR(120) NULL,
        EVENT_ID NVARCHAR(100) NULL,
        PAYLOAD_JSON NVARCHAR(MAX) NULL,
        ESTADO NVARCHAR(20) NOT NULL CONSTRAINT DF_WS_EVENT_QUEUE_ESTADO DEFAULT ('PENDIENTE'),
        FECHA_EVENTO DATETIME NOT NULL CONSTRAINT DF_WS_EVENT_QUEUE_FECHA_EVENTO DEFAULT (GETDATE()),
        TOMADO_EN DATETIME NULL,
        PROCESADO_EN DATETIME NULL,
        WORKER NVARCHAR(80) NULL,
        ERROR_MSG NVARCHAR(1000) NULL
    );

    CREATE INDEX IX_WS_EVENT_QUEUE_ESTADO_FECHA
        ON dbo.WS_EVENT_QUEUE (ESTADO, FECHA_EVENTO, ID_EVENTO);
END;
GO

CREATE OR ALTER PROCEDURE dbo.SP_WS_ENQUEUE_EVENT
    @CANAL NVARCHAR(60),
    @TIPO_EVENTO NVARCHAR(60),
    @DOCUMENT_ID NVARCHAR(80) = NULL,
    @ESTADO_DOC NVARCHAR(40) = NULL,
    @RAZON NVARCHAR(120) = NULL,
    @PAYLOAD_JSON NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.WS_EVENT_QUEUE (
        CANAL,
        TIPO_EVENTO,
        DOCUMENT_ID,
        ESTADO_DOC,
        RAZON,
        EVENT_ID,
        PAYLOAD_JSON
    )
    VALUES (
        @CANAL,
        @TIPO_EVENTO,
        @DOCUMENT_ID,
        @ESTADO_DOC,
        @RAZON,
        CONVERT(NVARCHAR(100), NEWID()),
        @PAYLOAD_JSON
    );
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_WS_CAB_PEDIDO
ON dbo.CAB_PEDIDO
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
    SELECT
        'prefacturas',
        CASE
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NULL THEN 'created'
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NOT NULL THEN 'updated'
            ELSE 'deleted'
        END,
        CAST(COALESCE(i.ID_DOC, d.ID_DOC) AS NVARCHAR(80)),
        CAST(COALESCE(i.EST_DOC, d.EST_DOC, '') AS NVARCHAR(40)),
        CASE
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NULL THEN 'db-created'
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NOT NULL THEN 'db-updated'
            ELSE 'db-deleted'
        END,
        CONVERT(NVARCHAR(100), NEWID()),
        (
            SELECT
                CAST(COALESCE(i.ID_DOC, d.ID_DOC) AS NVARCHAR(80)) AS document_id,
                CAST(COALESCE(i.EST_DOC, d.EST_DOC, '') AS NVARCHAR(40)) AS estado
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )
    FROM inserted i
    FULL OUTER JOIN deleted d
        ON i.ID_DOC = d.ID_DOC;
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_WS_CAB_FACTURA
ON dbo.CAB_FACTURA
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
    SELECT
        'facturas',
        CASE
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NULL THEN 'created'
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NOT NULL THEN 'updated'
            ELSE 'deleted'
        END,
        CAST(COALESCE(i.ID_DOC, d.ID_DOC) AS NVARCHAR(80)),
        CAST(COALESCE(i.EST_DOC, d.EST_DOC, '') AS NVARCHAR(40)),
        CASE
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NULL THEN 'db-created'
            WHEN i.ID_DOC IS NOT NULL AND d.ID_DOC IS NOT NULL THEN 'db-updated'
            ELSE 'db-deleted'
        END,
        CONVERT(NVARCHAR(100), NEWID()),
        (
            SELECT
                CAST(COALESCE(i.ID_DOC, d.ID_DOC) AS NVARCHAR(80)) AS document_id,
                CAST(COALESCE(i.EST_DOC, d.EST_DOC, '') AS NVARCHAR(40)) AS estado,
                CAST(COALESCE(i.TIPO_DOC, d.TIPO_DOC, '') AS NVARCHAR(20)) AS tipo_doc
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )
    FROM inserted i
    FULL OUTER JOIN deleted d
        ON i.ID_DOC = d.ID_DOC
    WHERE UPPER(CAST(COALESCE(i.TIPO_DOC, d.TIPO_DOC, '') AS NVARCHAR(20))) IN ('FC', 'FA');
END;
GO

DECLARE @cxc_doc_col SYSNAME;
DECLARE @cxc_no_col SYSNAME;
DECLARE @cxc_estado_col SYSNAME;
DECLARE @cxc_join_col SYSNAME;
DECLARE @cxc_sql NVARCHAR(MAX);

SET @cxc_doc_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_RECIBO') IS NOT NULL THEN 'ID_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_RECIBO') IS NOT NULL THEN 'NO_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    ELSE NULL
END;
SET @cxc_no_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_RECIBO') IS NOT NULL THEN 'NO_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_RECIBO') IS NOT NULL THEN 'ID_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    ELSE NULL
END;
SET @cxc_estado_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ESTATUS') IS NOT NULL THEN 'ESTATUS'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'EST_DOC') IS NOT NULL THEN 'EST_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ESTADO') IS NOT NULL THEN 'ESTADO'
    ELSE NULL
END;
SET @cxc_join_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_RECIBO') IS NOT NULL THEN 'ID_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_RECIBO') IS NOT NULL THEN 'NO_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    ELSE NULL
END;

IF @cxc_doc_col IS NOT NULL AND @cxc_no_col IS NOT NULL AND @cxc_join_col IS NOT NULL
BEGIN
    SET @cxc_sql = N'
    CREATE OR ALTER TRIGGER dbo.TR_WS_CAB_RECIBO_INGRESO
    ON dbo.CAB_RECIBO_INGRESO
    AFTER INSERT, UPDATE, DELETE
    AS
    BEGIN
        SET NOCOUNT ON;

        INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
        SELECT
            ''cxc'',
            CASE
                WHEN i.[' + @cxc_join_col + N'] IS NOT NULL AND d.[' + @cxc_join_col + N'] IS NULL THEN ''created''
                WHEN i.[' + @cxc_join_col + N'] IS NOT NULL AND d.[' + @cxc_join_col + N'] IS NOT NULL THEN ''updated''
                ELSE ''deleted''
            END,
            CAST(COALESCE(i.[' + @cxc_doc_col + N'], d.[' + @cxc_doc_col + N']) AS NVARCHAR(80)),
            ' + CASE WHEN @cxc_estado_col IS NOT NULL
                THEN N'CAST(COALESCE(i.[' + @cxc_estado_col + N'], d.[' + @cxc_estado_col + N'], '''') AS NVARCHAR(40))'
                ELSE N'CAST('''' AS NVARCHAR(40))'
            END + N',
            CASE
                WHEN i.[' + @cxc_join_col + N'] IS NOT NULL AND d.[' + @cxc_join_col + N'] IS NULL THEN ''db-created''
                WHEN i.[' + @cxc_join_col + N'] IS NOT NULL AND d.[' + @cxc_join_col + N'] IS NOT NULL THEN ''db-updated''
                ELSE ''db-deleted''
            END,
            CONVERT(NVARCHAR(100), NEWID()),
            (
                SELECT
                    CAST(COALESCE(i.[' + @cxc_doc_col + N'], d.[' + @cxc_doc_col + N']) AS NVARCHAR(80)) AS document_id,
                    CAST(COALESCE(i.[' + @cxc_no_col + N'], d.[' + @cxc_no_col + N']) AS NVARCHAR(80)) AS no_recibo,
                    ' + CASE WHEN @cxc_estado_col IS NOT NULL
                        THEN N'CAST(COALESCE(i.[' + @cxc_estado_col + N'], d.[' + @cxc_estado_col + N'], '''') AS NVARCHAR(40))'
                        ELSE N'CAST('''' AS NVARCHAR(40))'
                    END + N' AS estado
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            )
        FROM inserted i
        FULL OUTER JOIN deleted d
            ON i.[' + @cxc_join_col + N'] = d.[' + @cxc_join_col + N'];
    END;';
    EXEC sys.sp_executesql @cxc_sql;
END;
GO

DECLARE @cxc_cliente_col SYSNAME;
DECLARE @cxc_nombre_col SYSNAME;
DECLARE @cxc_total_col SYSNAME;
DECLARE @cxc_doc_col_pago SYSNAME;
DECLARE @cxc_no_col_pago SYSNAME;
DECLARE @acuerdo_pago_sql NVARCHAR(MAX);

SET @cxc_doc_col_pago = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_RECIBO') IS NOT NULL THEN 'ID_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_RECIBO') IS NOT NULL THEN 'NO_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    ELSE NULL
END;
SET @cxc_no_col_pago = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_RECIBO') IS NOT NULL THEN 'NO_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_RECIBO') IS NOT NULL THEN 'ID_RECIBO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    ELSE NULL
END;
SET @cxc_cliente_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'ID_SN') IS NOT NULL THEN 'ID_SN'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'CLIENTE') IS NOT NULL THEN 'CLIENTE'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'COD_CLIENTE') IS NOT NULL THEN 'COD_CLIENTE'
    ELSE NULL
END;
SET @cxc_nombre_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NOM_SN') IS NOT NULL THEN 'NOM_SN'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NOM_SOCIO') IS NOT NULL THEN 'NOM_SOCIO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NOMBRE') IS NOT NULL THEN 'NOMBRE'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'NOM_CLIENTE') IS NOT NULL THEN 'NOM_CLIENTE'
    ELSE NULL
END;
SET @cxc_total_col = CASE
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'TOTAL_COBRO') IS NOT NULL THEN 'TOTAL_COBRO'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'TOTAL_DOC') IS NOT NULL THEN 'TOTAL_DOC'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'IMPORTE') IS NOT NULL THEN 'IMPORTE'
    WHEN COL_LENGTH('dbo.CAB_RECIBO_INGRESO', 'MONTO') IS NOT NULL THEN 'MONTO'
    ELSE NULL
END;

IF @cxc_cliente_col IS NOT NULL AND @cxc_doc_col_pago IS NOT NULL AND @cxc_no_col_pago IS NOT NULL
BEGIN
    SET @acuerdo_pago_sql = N'
    CREATE OR ALTER TRIGGER dbo.TR_WS_CAB_RECIBO_INGRESO_ACUERDO_PAGO
    ON dbo.CAB_RECIBO_INGRESO
    AFTER INSERT
    AS
    BEGIN
        SET NOCOUNT ON;

        IF OBJECT_ID(''dbo.COBRO_ACUERDO'', ''U'') IS NULL
        BEGIN
            RETURN;
        END;

        INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
        SELECT
            ''notifications'',
            ''agreement_payment_received'',
            CAST(i.[' + @cxc_doc_col_pago + N'] AS NVARCHAR(80)),
            ''PAGADO'',
            ''agreement-payment-received'',
            CONVERT(NVARCHAR(100), NEWID()),
            (
                SELECT
                    CAST(a.ID_ACUERDO AS NVARCHAR(50)) AS acuerdo_id,
                    CAST(i.[' + @cxc_doc_col_pago + N'] AS NVARCHAR(80)) AS document_id,
                    CAST(i.[' + @cxc_no_col_pago + N'] AS NVARCHAR(80)) AS no_recibo,
                    CAST(i.[' + @cxc_cliente_col + N'] AS NVARCHAR(30)) AS id_sn,
                    ' + CASE WHEN @cxc_nombre_col IS NOT NULL
                        THEN N'CAST(i.[' + @cxc_nombre_col + N'] AS NVARCHAR(200))'
                        ELSE N'CAST('''' AS NVARCHAR(200))'
                    END + N' AS cliente_nombre,
                    CAST(a.TIPO AS NVARCHAR(30)) AS tipo_acuerdo,
                    CONVERT(NVARCHAR(10), a.FECHA_COMPROMISO, 23) AS fecha_compromiso,
                    ' + CASE WHEN @cxc_total_col IS NOT NULL
                        THEN N'CAST(ISNULL(i.[' + @cxc_total_col + N'], 0) AS DECIMAL(19,2))'
                        ELSE N'CAST(0 AS DECIMAL(19,2))'
                    END + N' AS monto_pago
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            )
        FROM inserted i
        CROSS APPLY (
            SELECT TOP 1 a.*
            FROM dbo.COBRO_ACUERDO a
            WHERE CAST(a.ID_SN AS NVARCHAR(50)) = CAST(i.[' + @cxc_cliente_col + N'] AS NVARCHAR(50))
              AND UPPER(ISNULL(a.ESTADO, '''')) = ''PENDIENTE''
            ORDER BY
                CASE WHEN a.FECHA_COMPROMISO IS NULL THEN 1 ELSE 0 END,
                a.FECHA_COMPROMISO,
                a.FECHA_CREACION DESC,
                a.ID_ACUERDO DESC
        ) a
        WHERE CAST(i.[' + @cxc_cliente_col + N'] AS NVARCHAR(50)) <> '''';
    END;';
    EXEC sys.sp_executesql @acuerdo_pago_sql;
END;
GO

DECLARE @prest_doc_col SYSNAME;
DECLARE @prest_estado_col SYSNAME;
DECLARE @prest_join_col SYSNAME;
DECLARE @prest_sql NVARCHAR(MAX);

SET @prest_doc_col = CASE
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'DOCUMENTO') IS NOT NULL THEN 'DOCUMENTO'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'FACTURA') IS NOT NULL THEN 'FACTURA'
    ELSE NULL
END;
SET @prest_estado_col = CASE
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'EST_DOC') IS NOT NULL THEN 'EST_DOC'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'ESTATUS') IS NOT NULL THEN 'ESTATUS'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'ESTADO') IS NOT NULL THEN 'ESTADO'
    ELSE NULL
END;
SET @prest_join_col = CASE
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'ID_PRESTAMO') IS NOT NULL THEN 'ID_PRESTAMO'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'NO_PRESTAMO') IS NOT NULL THEN 'NO_PRESTAMO'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'NO') IS NOT NULL THEN 'NO'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'NO_DOC') IS NOT NULL THEN 'NO_DOC'
    WHEN COL_LENGTH('dbo.CAB_PRESTAMO', 'ID_DOC') IS NOT NULL THEN 'ID_DOC'
    ELSE NULL
END;

IF @prest_doc_col IS NOT NULL AND @prest_join_col IS NOT NULL
BEGIN
    SET @prest_sql = N'
    CREATE OR ALTER TRIGGER dbo.TR_WS_CAB_PRESTAMO
    ON dbo.CAB_PRESTAMO
    AFTER INSERT, UPDATE, DELETE
    AS
    BEGIN
        SET NOCOUNT ON;

        INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
        SELECT
            ''financiamiento'',
            CASE
                WHEN i.[' + @prest_join_col + N'] IS NOT NULL AND d.[' + @prest_join_col + N'] IS NULL THEN ''created''
                WHEN i.[' + @prest_join_col + N'] IS NOT NULL AND d.[' + @prest_join_col + N'] IS NOT NULL THEN ''updated''
                ELSE ''deleted''
            END,
            CAST(COALESCE(i.[' + @prest_doc_col + N'], d.[' + @prest_doc_col + N']) AS NVARCHAR(80)),
            ' + CASE WHEN @prest_estado_col IS NOT NULL
                THEN N'CAST(COALESCE(i.[' + @prest_estado_col + N'], d.[' + @prest_estado_col + N'], '''') AS NVARCHAR(40))'
                ELSE N'CAST('''' AS NVARCHAR(40))'
            END + N',
            CASE
                WHEN i.[' + @prest_join_col + N'] IS NOT NULL AND d.[' + @prest_join_col + N'] IS NULL THEN ''db-created''
                WHEN i.[' + @prest_join_col + N'] IS NOT NULL AND d.[' + @prest_join_col + N'] IS NOT NULL THEN ''db-updated''
                ELSE ''db-deleted''
            END,
            CONVERT(NVARCHAR(100), NEWID()),
            (
                SELECT
                    CAST(COALESCE(i.[' + @prest_doc_col + N'], d.[' + @prest_doc_col + N']) AS NVARCHAR(80)) AS document_id,
                    CAST(COALESCE(i.[' + @prest_doc_col + N'], d.[' + @prest_doc_col + N']) AS NVARCHAR(80)) AS factura_no,
                    ' + CASE WHEN @prest_estado_col IS NOT NULL
                        THEN N'CAST(COALESCE(i.[' + @prest_estado_col + N'], d.[' + @prest_estado_col + N'], '''') AS NVARCHAR(40))'
                        ELSE N'CAST('''' AS NVARCHAR(40))'
                    END + N' AS estado
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            )
        FROM inserted i
        FULL OUTER JOIN deleted d
            ON i.[' + @prest_join_col + N'] = d.[' + @prest_join_col + N'];
    END;';
    EXEC sys.sp_executesql @prest_sql;
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_WS_INV_SOLICITUD_EXISTENCIA
ON dbo.INV_SOLICITUD_EXISTENCIA
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.WS_EVENT_QUEUE (CANAL, TIPO_EVENTO, DOCUMENT_ID, ESTADO_DOC, RAZON, EVENT_ID, PAYLOAD_JSON)
    SELECT
        'inventario_solicitudes',
        CASE
            WHEN i.ID_SOLICITUD IS NOT NULL AND d.ID_SOLICITUD IS NULL THEN 'created'
            WHEN i.ID_SOLICITUD IS NOT NULL AND d.ID_SOLICITUD IS NOT NULL THEN 'updated'
            ELSE 'deleted'
        END,
        CAST(COALESCE(i.ID_SOLICITUD, d.ID_SOLICITUD) AS NVARCHAR(80)),
        CASE
            WHEN COALESCE(i.ATENDIDA, d.ATENDIDA, 0) = 1 THEN 'ATENDIDA'
            ELSE 'PENDIENTE'
        END,
        CASE
            WHEN i.ID_SOLICITUD IS NOT NULL AND d.ID_SOLICITUD IS NULL THEN 'db-created'
            WHEN i.ID_SOLICITUD IS NOT NULL AND d.ID_SOLICITUD IS NOT NULL THEN 'db-updated'
            ELSE 'db-deleted'
        END,
        CONVERT(NVARCHAR(100), NEWID()),
        (
            SELECT
                CAST(COALESCE(i.ID_SOLICITUD, d.ID_SOLICITUD) AS NVARCHAR(80)) AS document_id,
                CASE
                    WHEN COALESCE(i.ATENDIDA, d.ATENDIDA, 0) = 1 THEN 'ATENDIDA'
                    ELSE 'PENDIENTE'
                END AS estado
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )
    FROM inserted i
    FULL OUTER JOIN deleted d
        ON i.ID_SOLICITUD = d.ID_SOLICITUD;
END;
GO
