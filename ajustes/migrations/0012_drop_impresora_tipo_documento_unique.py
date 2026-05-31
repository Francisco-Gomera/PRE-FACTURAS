from django.db import migrations


DROP_TIPO_DOCUMENTO_UNIQUE_SQL = r"""
DECLARE @sql NVARCHAR(MAX) = N'';

SELECT @sql = @sql + N'ALTER TABLE [AJUSTE_IMPRESORA_CONFIG] DROP CONSTRAINT [' + kc.[name] + N'];'
FROM sys.key_constraints kc
JOIN sys.tables t ON kc.parent_object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.[name] = N'AJUSTE_IMPRESORA_CONFIG'
  AND kc.[type] = N'UQ'
  AND kc.[name] <> N'uq_impresora_terminal_tipo'
  AND NOT EXISTS (
      SELECT 1
      FROM sys.index_columns ic
      JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
      WHERE ic.object_id = kc.parent_object_id
        AND ic.index_id = kc.unique_index_id
        AND c.[name] <> N'TIPO_DOCUMENTO'
  )
  AND EXISTS (
      SELECT 1
      FROM sys.index_columns ic
      JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
      WHERE ic.object_id = kc.parent_object_id
        AND ic.index_id = kc.unique_index_id
        AND c.[name] = N'TIPO_DOCUMENTO'
  );

SELECT @sql = @sql + N'DROP INDEX [' + i.[name] + N'] ON [AJUSTE_IMPRESORA_CONFIG];'
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.[name] = N'AJUSTE_IMPRESORA_CONFIG'
  AND i.is_unique = 1
  AND i.is_primary_key = 0
  AND i.[name] <> N'uq_impresora_terminal_tipo'
  AND NOT EXISTS (
      SELECT 1
      FROM sys.index_columns ic
      JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
      WHERE ic.object_id = i.object_id
        AND ic.index_id = i.index_id
        AND c.[name] <> N'TIPO_DOCUMENTO'
  )
  AND EXISTS (
      SELECT 1
      FROM sys.index_columns ic
      JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
      WHERE ic.object_id = i.object_id
        AND ic.index_id = i.index_id
        AND c.[name] = N'TIPO_DOCUMENTO'
  );

IF LEN(@sql) > 0
BEGIN
    EXEC sp_executesql @sql;
END
"""


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0011_impresora_config_terminal"),
    ]

    operations = [
        migrations.RunSQL(DROP_TIPO_DOCUMENTO_UNIQUE_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
