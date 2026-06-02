import sys
import os

file_path = r'c:\PRE-FACTURAS\empleados\templates\empleados\acciones_personal.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if (["VACACIONES", "SUSPENCION", "LICENCIA MEDICA"].includes(cambioMotivo)) {',
    'if (["VACACIONES", "SUSPENCION", "LICENCIA MEDICA", "PERMISO"].includes(cambioMotivo)) {'
)
content = content.replace(
    'cambioLicenciaMedicaDesdeField.value = action.cambio_motivo === "LICENCIA MEDICA" ? action.fecha_desde || "" : "";',
    'cambioLicenciaMedicaDesdeField.value = action.cambio_motivo === "LICENCIA MEDICA" || action.cambio_motivo === "PERMISO" ? action.fecha_desde || "" : "";'
)
content = content.replace(
    'cambioLicenciaMedicaHastaField.value = action.cambio_motivo === "LICENCIA MEDICA" ? action.fecha_hasta || "" : "";',
    'cambioLicenciaMedicaHastaField.value = action.cambio_motivo === "LICENCIA MEDICA" || action.cambio_motivo === "PERMISO" ? action.fecha_hasta || "" : "";'
)
content = content.replace(
    'fecha_desde: cambioMotivo === "SUSPENCION" ? cambioSuspensionDesdeField.value : cambioMotivo === "VACACIONES" ? cambioVacacionesDesdeField.value : cambioMotivo === "LICENCIA MEDICA" ? cambioLicenciaMedicaDesdeField.value : "",',
    'fecha_desde: cambioMotivo === "SUSPENCION" ? cambioSuspensionDesdeField.value : cambioMotivo === "VACACIONES" ? cambioVacacionesDesdeField.value : cambioMotivo === "LICENCIA MEDICA" || cambioMotivo === "PERMISO" ? cambioLicenciaMedicaDesdeField.value : "",'
)
content = content.replace(
    'fecha_hasta: cambioMotivo === "SUSPENCION" ? cambioSuspensionHastaField.value : cambioMotivo === "VACACIONES" ? cambioVacacionesHastaField.value : cambioMotivo === "LICENCIA MEDICA" ? cambioLicenciaMedicaHastaField.value : "",',
    'fecha_hasta: cambioMotivo === "SUSPENCION" ? cambioSuspensionHastaField.value : cambioMotivo === "VACACIONES" ? cambioVacacionesHastaField.value : cambioMotivo === "LICENCIA MEDICA" || cambioMotivo === "PERMISO" ? cambioLicenciaMedicaHastaField.value : "",'
)
content = content.replace(
    'cantidad_dias: cambioMotivo === "VACACIONES" ? cambioVacacionesSolicitadosField.value : cambioMotivo === "LICENCIA MEDICA" ? cambioLicenciaMedicaDiasField.value : "",',
    'cantidad_dias: cambioMotivo === "VACACIONES" ? cambioVacacionesSolicitadosField.value : cambioMotivo === "LICENCIA MEDICA" || cambioMotivo === "PERMISO" ? cambioLicenciaMedicaDiasField.value : "",'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML patched")
