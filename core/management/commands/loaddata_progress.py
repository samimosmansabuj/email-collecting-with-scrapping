from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.conf import settings

import io
import json
import os

# tqdm optional import
try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# ijson optional import (memory efficient counting)
try:
    import ijson
except Exception:
    ijson = None


class Command(BaseCommand):
    help = "Load JSON fixture with a progress bar (like loaddata but shows progress)."

    def add_arguments(self, parser):
        parser.add_argument("fixture_path", type=str, help="Path to JSON fixture file")
        parser.add_argument(
            "--database", default=DEFAULT_DB_ALIAS, help="Database alias (default: default)"
        )
        parser.add_argument(
            "--batch-size", type=int, default=50,
            help="(Hint only) Number of objects per internal save chunk; progress updates every object."
        )
        parser.add_argument(
            "--non-atomic", action="store_true",
            help="Do NOT wrap in a single atomic transaction (commits as it goes)."
        )
        parser.add_argument(
            "--encoding", default="utf-8",
            help="File encoding (default: utf-8)."
        )

    def _count_items(self, path, encoding):
        if ijson is not None:
            with open(path, "rb") as f:  # open in binary for ijson
                count = 0
                # Each top-level item is a fixture object
                for _ in ijson.items(f, "item"):
                    count += 1
                return count, True

        # Fallback: load once (might be heavy for very large files)
        with io.open(path, "r", encoding=encoding, errors="strict") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise CommandError(f"Invalid JSON: {e}")
            if not isinstance(data, list):
                raise CommandError("Expected top-level JSON array of fixtures.")
            return len(data), False

    def handle(self, *args, **options):
        fixture_path = options["fixture_path"]
        db_alias = options["database"]
        encoding = options["encoding"]
        non_atomic = options["non_atomic"]

        if not os.path.exists(fixture_path):
            raise CommandError(f"File not found: {fixture_path}")

        # Count total items for progress bar
        try:
            total, streaming = self._count_items(fixture_path, encoding)
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f"Failed to count items: {e}")

        if total == 0:
            self.stdout.write(self.style.WARNING("No items found in the fixture. Nothing to load."))
            return

        self.stdout.write(self.style.NOTICE(
            f"Loading {total} objects from {fixture_path} "
            f"({'streaming count' if streaming else 'loaded count'}) "
            f"into database '{db_alias}'..."
        ))

        # Prepare progress bar
        use_tqdm = tqdm is not None
        pbar = tqdm(total=total, unit="obj") if use_tqdm else None

        # Open file for deserialization (text mode for Django serializers)
        try:
            f = io.open(fixture_path, "r", encoding=encoding, errors="strict")
        except Exception as e:
            if pbar: pbar.close()
            raise CommandError(f"Failed to open file: {e}")

        # Deserializer is a generator of DeserializedObject
        try:
            objects = serializers.deserialize("json", f, ignorenonexistent=False, stream=True)
        except Exception as e:
            if pbar: pbar.close()
            f.close()
            raise CommandError(f"Failed to start deserialization: {e}")

        # Wrap in a single atomic transaction unless --non-atomic is given
        connection = connections[db_alias]

        def _save_all():
            saved = 0
            for obj in objects:
                obj.save(using=db_alias)  # saves model and its M2M after pk exists
                saved += 1
                if pbar:
                    pbar.update(1)
                elif saved % 50 == 0:
                    # Lightweight progress when tqdm not available
                    self.stdout.write(f"{saved}/{total} loaded...")
            return saved

        try:
            if non_atomic:
                # Constraints disabled still helps speed & integrity, but commits as we go
                with connection.constraint_checks_disabled():
                    saved = _save_all()
                    connection.check_constraints()
            else:
                with transaction.atomic(using=db_alias):
                    with connection.constraint_checks_disabled():
                        saved = _save_all()
                        connection.check_constraints()
        except Exception as e:
            if pbar: pbar.close()
            f.close()
            raise CommandError(f"Load failed: {e}")

        if pbar: pbar.close()
        f.close()

        self.stdout.write(self.style.SUCCESS(f"Done. Loaded {saved}/{total} objects."))
