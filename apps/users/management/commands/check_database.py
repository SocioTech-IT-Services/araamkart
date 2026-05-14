"""Verify the default DB connection (e.g. Supabase). Never prints passwords."""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "Run SELECT 1 on the default database. Use --migrate to apply migrations after a successful check."

    def add_arguments(self, parser):
        parser.add_argument(
            "--migrate",
            action="store_true",
            help="Run migrate (non-interactive) after the connection check succeeds.",
        )

    def handle(self, *args, **options):
        conn = connections["default"]
        cfg = conn.settings_dict
        self.stdout.write(f"ENGINE: {cfg.get('ENGINE')}")
        self.stdout.write(f"HOST:   {cfg.get('HOST')}")
        self.stdout.write(f"PORT:   {cfg.get('PORT')}")
        self.stdout.write(f"NAME:   {cfg.get('NAME')}")
        self.stdout.write(f"USER:   {cfg.get('USER')}")
        self.stdout.write(f"PASSWORD set: {'yes' if cfg.get('PASSWORD') else 'no'}")
        if cfg.get("DISABLE_SERVER_SIDE_CURSORS"):
            self.stdout.write("DISABLE_SERVER_SIDE_CURSORS: True (transaction pooler)")
        sslm = (cfg.get("OPTIONS") or {}).get("sslmode")
        if sslm:
            self.stdout.write(f"sslmode: {sslm}")

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                one = cursor.fetchone()[0]
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Connection failed: {exc}"))
            raise SystemExit(1) from exc

        self.stdout.write(self.style.SUCCESS(f"OK: SELECT 1 -> {one}"))

        if options["migrate"]:
            self.stdout.write("Running migrate...")
            call_command("migrate", interactive=False)
            self.stdout.write(self.style.SUCCESS("migrate finished."))
