from .models import FormatoImpresionConfig


DEFAULT_PRINT_FORMATS = {
    FormatoImpresionConfig.DOCUMENTO_RECIBO_PAGO: FormatoImpresionConfig.FORMATO_A4,
    FormatoImpresionConfig.DOCUMENTO_FACTURA: FormatoImpresionConfig.FORMATO_A4,
}


def get_print_format(documento):
    documento = str(documento or "").strip()
    fallback = DEFAULT_PRINT_FORMATS.get(documento, FormatoImpresionConfig.FORMATO_A4)
    try:
        config, _ = FormatoImpresionConfig.objects.get_or_create(
            documento=documento,
            defaults={"formato": fallback},
        )
        if config.formato in {
            FormatoImpresionConfig.FORMATO_A4,
            FormatoImpresionConfig.FORMATO_80MM,
            FormatoImpresionConfig.FORMATO_58MM,
        }:
            return config.formato
    except Exception:
        pass
    return fallback


def get_print_format_label(formato):
    return {
        FormatoImpresionConfig.FORMATO_A4: "A4",
        FormatoImpresionConfig.FORMATO_80MM: "80mm",
        FormatoImpresionConfig.FORMATO_58MM: "58mm",
    }.get(str(formato or "").strip(), "A4")
