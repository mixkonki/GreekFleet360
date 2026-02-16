"""
Tenant Guardrails Tests
Ensures unauthorized use of all_objects is prevented
"""
from django.test import TestCase
from core.models import Company
from core.mixins import get_current_company
from core.tenant_context import tenant_context
from finance.models import CompanyExpense, ExpenseCategory, ExpenseFamily
import os
import re


class TenantGuardrailsTestCase(TestCase):
    """
    Test suite for tenant guardrails
    
    Verifies that:
    1. all_objects is only used in authorized locations
    2. tenant_context manager works correctly
    3. Context cleanup happens even on exceptions
    """
    
    def test_no_unauthorized_all_objects_usage(self):
        """
        Scan project for unauthorized use of all_objects
        
        Allowlist:
        - admin.py (admin needs unscoped access)
        - tests/ (tests need to create cross-tenant data)
        - migrations/ (migrations are schema-only)
        - core/tenant_context.py (context manager implementation)
        - core/mixins.py (manager definition)
        """
        # Define allowlist patterns
        allowlist_patterns = [
            r'admin\.py$',
            r'tests[/\\]',
            r'migrations[/\\]',
            r'core[/\\]tenant_context\.py$',
            r'core[/\\]mixins\.py$',
            r'models\.py$',  # Model definitions need all_objects manager
        ]
        
        # Get project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Scan for all_objects usage
        violations = []
        
        for root, dirs, files in os.walk(project_root):
            # Skip virtual environment and git directories
            dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', 'env', '.git', '__pycache__']]
            
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                filepath = os.path.join(root, file)
                relative_path = os.path.relpath(filepath, project_root)
                
                # Check if file is in allowlist
                is_allowed = any(re.search(pattern, relative_path.replace('\\', '/')) for pattern in allowlist_patterns)
                
                if is_allowed:
                    continue
                
                # Scan file for all_objects usage
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Look for all_objects usage
                        if 'all_objects' in content:
                            # Find line numbers
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                if 'all_objects' in line and not line.strip().startswith('#'):
                                    violations.append({
                                        'file': relative_path,
                                        'line': line_num,
                                        'content': line.strip()
                                    })
                except Exception:
                    # Skip files that can't be read
                    pass
        
        # Assert no violations found
        if violations:
            error_msg = "Unauthorized use of all_objects found:\n"
            for v in violations:
                error_msg += f"\n  {v['file']}:{v['line']}\n    {v['content']}\n"
            error_msg += "\nall_objects should only be used in admin.py, tests/, migrations/, core/tenant_context.py, and core/mixins.py"
            self.fail(error_msg)
    
    def test_tenant_context_sets_company(self):
        """
        Test that tenant_context correctly sets company
        """
        # Create test company
        company = Company.objects.create(
            name="Test Company",
            tax_id="999999999",
            transport_type="FREIGHT"
        )
        
        # Verify no company is set initially
        self.assertIsNone(get_current_company())
        
        # Use context manager
        with tenant_context(company):
            # Verify company is set inside context
            current = get_current_company()
            self.assertEqual(current, company)
        
        # Verify company is cleared after context
        self.assertIsNone(get_current_company())
    
    def test_tenant_context_cleanup_on_exception(self):
        """
        Test that tenant_context cleans up even when exception occurs
        """
        # Create test company
        company = Company.objects.create(
            name="Test Company 2",
            tax_id="888888888",
            transport_type="FREIGHT"
        )
        
        # Verify no company is set initially
        self.assertIsNone(get_current_company())
        
        # Use context manager with exception
        try:
            with tenant_context(company):
                # Verify company is set
                self.assertEqual(get_current_company(), company)
                
                # Raise exception
                raise ValueError("Test exception")
        except ValueError:
            # Exception is expected
            pass
        
        # Verify company is still cleared after exception
        self.assertIsNone(get_current_company())
    
    def test_tenant_context_with_queries(self):
        """
        Test that tenant_context works with actual queries
        """
        # Create two companies
        company_a = Company.objects.create(
            name="Context Company A",
            tax_id="777777777",
            transport_type="FREIGHT"
        )
        
        company_b = Company.objects.create(
            name="Context Company B",
            tax_id="666666666",
            transport_type="FREIGHT"
        )
        
        # Create expense family and category
        family = ExpenseFamily.objects.create(
            name="Context Test Family",
            display_order=1
        )
        category = ExpenseCategory.objects.create(
            family=family,
            name="Context Test Category",
            is_system_default=True
        )
        
        # Create expenses for both companies using all_objects
        expense_a = CompanyExpense.all_objects.create(
            company=company_a,
            category=category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=1000.00,
            start_date='2026-01-01'
        )
        
        expense_b = CompanyExpense.all_objects.create(
            company=company_b,
            category=category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=2000.00,
            start_date='2026-01-01'
        )
        
        # Test with Company A context
        with tenant_context(company_a):
            expenses = CompanyExpense.objects.all()
            self.assertEqual(expenses.count(), 1)
            self.assertEqual(expenses.first().id, expense_a.id)
        
        # Test with Company B context
        with tenant_context(company_b):
            expenses = CompanyExpense.objects.all()
            self.assertEqual(expenses.count(), 1)
            self.assertEqual(expenses.first().id, expense_b.id)
        
        # Test with no context
        expenses = CompanyExpense.objects.all()
        self.assertEqual(expenses.count(), 0)
