"""
Management Command: calculate_costs

Runs the Cost Engine for a specified period and optionally
persists calculation results to the database.
"""

from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError

from core.models import Company
from core.tenant_context import tenant_context
from finance.services.cost_engine import calculate_company_costs
from finance.services.cost_engine.persist import CostEnginePersistence


class Command(BaseCommand):
    help = "Calculate company costs for a period and save snapshots"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            required=True,
            help="Company name or ID",
        )

        parser.add_argument(
            "--period",
            type=str,
            default="current",
            help='Period format YYYY-MM or "current"',
        )

        parser.add_argument(
            "--basis",
            type=str,
            choices=["KM", "HOUR", "TRIP", "REVENUE"],
            default="KM",
            help="Allocation basis unit (used by calculator output / breakdowns)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run calculations without saving results",
        )

    def handle(self, *args, **options):
        company_identifier = options["company"]
        period_str = options["period"]
        basis_unit = options["basis"]
        dry_run = options["dry_run"]

        # -----------------------------------------------------
        # Resolve company
        # -----------------------------------------------------
        try:
            if company_identifier.isdigit():
                company = Company.objects.get(id=int(company_identifier))
            else:
                company = Company.objects.get(name__iexact=company_identifier)
        except Company.DoesNotExist:
            raise CommandError(f'Company "{company_identifier}" not found')

        self.stdout.write(self.style.SUCCESS(f"Company: {company.name}"))

        # -----------------------------------------------------
        # Parse period
        # -----------------------------------------------------
        if period_str.lower() == "current":
            today = date.today()
            period_start = date(today.year, today.month, 1)
        else:
            try:
                parsed = datetime.strptime(period_str, "%Y-%m")
                period_start = date(parsed.year, parsed.month, 1)
            except ValueError as exc:
                raise CommandError('Invalid period format. Use YYYY-MM or "current"') from exc

        period_end = period_start + relativedelta(months=1) - relativedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"Period: {period_start} → {period_end}"))
        self.stdout.write(self.style.SUCCESS(f"Basis Unit: {basis_unit}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE — nothing will be saved"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Starting Cost Engine Calculation...")
        self.stdout.write("=" * 60 + "\n")

        # -----------------------------------------------------
        # Run Cost Engine
        # -----------------------------------------------------
        try:
            # Activate tenant scope for scoped managers + auto-assign
            with tenant_context(company):
                result = calculate_company_costs(company, period_start, period_end)

            snapshots = result.get("snapshots", []) or []
            breakdowns = result.get("breakdowns", []) or []
            summary = result.get("summary", {}) or {}

            # -------------------------------------------------
            # Output summary
            # -------------------------------------------------
            self.stdout.write(self.style.SUCCESS(f"✓ Snapshots calculated: {len(snapshots)}"))
            self.stdout.write(self.style.SUCCESS(f"✓ Order breakdowns calculated: {len(breakdowns)}"))

            if summary:
                self.stdout.write("Summary:")
                for key, value in summary.items():
                    self.stdout.write(f"  {key}: {value}")

            # -------------------------------------------------
            # Dry run stops here
            # -------------------------------------------------
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN — results not persisted"))
                return

            # -------------------------------------------------
            # Persist results
            # NOTE: Your persist layer signatures expect ONLY:
            #   save_cost_rate_snapshots(self, company, period_start, period_end, ...)
            # so we do NOT pass basis_unit here.
            # -------------------------------------------------
            self.stdout.write("\nSaving results to database...")

            persistence = CostEnginePersistence()

            # IMPORTANT: pass exactly what persist.py expects.
            # If your persist layer expects "cost_center_rates" (dict) instead of "snapshots" (list),
            # it should be updated there. Based on your current errors, it does NOT accept basis_unit.
            saved_snaps = persistence.save_cost_rate_snapshots(
                company,
                period_start,
                period_end,
                snapshots,
            )

            saved_breakdowns = persistence.save_order_cost_breakdowns(
                company,
                period_start,
                period_end,
                breakdowns,
            )

            self.stdout.write(self.style.SUCCESS(f"✓ Saved snapshots: {len(saved_snaps)}"))
            self.stdout.write(self.style.SUCCESS(f"✓ Saved breakdowns: {len(saved_breakdowns)}"))

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("✓ Cost Engine completed successfully"))
            self.stdout.write("=" * 60)

        except Exception as exc:
            raise CommandError(f"Calculation failed: {exc}") from exc
