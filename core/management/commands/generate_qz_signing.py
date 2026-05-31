from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Genera el certificado y la llave privada usados para firmar mensajes de QZ Tray."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes.")

    def handle(self, *args, **options):
        cert_path = settings.QZ_CERTIFICATE_PATH
        key_path = settings.QZ_PRIVATE_KEY_PATH
        if not options["force"] and (cert_path.exists() or key_path.exists()):
            self.stdout.write(self.style.WARNING("Los archivos de firma QZ ya existen. Usa --force para regenerarlos."))
            self.stdout.write(str(cert_path))
            self.stdout.write(str(key_path))
            return

        cert_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "DO"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CA ERP"),
            x509.NameAttribute(NameOID.COMMON_NAME, "CA ERP QZ Tray Signing"),
        ])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        key_path.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

        self.stdout.write(self.style.SUCCESS("Firma QZ generada correctamente."))
        self.stdout.write(str(cert_path))
        self.stdout.write(str(key_path))
