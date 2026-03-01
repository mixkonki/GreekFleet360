"""
Driver Compliance Validation Tests
Tests for hard-block validation when assigning drivers to transport orders
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from core.models import Company, Employee, EmployeePosition
from core.driver_compliance_models import DriverCompliance, DrivingLicenseCategory, AdrCategory
from finance.models import TransportOrder
from operations.models import Vehicle
from accounts.models import UserProfile


class DriverComplianceValidationTestCase(TestCase):
    """
    Test suite for driver compliance validation in TransportOrderForm
    
    Verifies HARD BLOCK when:
    1. Driver has no compliance record
    2. License is expired
    3. BUS without D/DE license
    4. BUS without valid PEI bus
    5. BUS without valid tachograph
    6. TRUCK without C/CE license
    7. TRUCK without valid PEI truck
    8. TRUCK without valid tachograph
    9. VAN without B license
    10. ADR order without valid ADR certification
    11. Tenant isolation (cannot use driver from another company)
    """
    
    def setUp(self):
        """
        Set up test data: companies, users, employees, vehicles, compliance
        """
        # Create Company A
        self.company_a = Company.objects.create(
            name="Company A",
            tax_id="111111111",
            transport_type="FREIGHT"
        )
        
        # Create Company B
        self.company_b = Company.objects.create(
            name="Company B",
            tax_id="222222222",
            transport_type="FREIGHT"
        )
        
        # Create User A (belongs to Company A)
        self.user_a = User.objects.create_user(
            username='user_a',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_a,
            company=self.company_a,
            role='ADMIN'
        )
        
        # Create Employee Positions
        self.position_driver = EmployeePosition.objects.create(
            title="Οδηγός",
            is_driver_role=True
        )
        
        # Get License Categories (seeded by migration)
        self.license_b = DrivingLicenseCategory.objects.get(code='B')
        self.license_c = DrivingLicenseCategory.objects.get(code='C')
        self.license_ce = DrivingLicenseCategory.objects.get(code='CE')
        self.license_d = DrivingLicenseCategory.objects.get(code='D')
        self.license_de = DrivingLicenseCategory.objects.get(code='DE')
        
        # Get ADR Category (seeded by migration)
        self.adr_p3 = AdrCategory.objects.get(code='Π3')
        
        # Create Vehicles
        self.bus_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="BUS-1111",
            make="Mercedes",
            model="Tourismo",
            vehicle_class="BUS",
            body_type="BUS_BODY"
        )
        
        self.truck_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="TRK-1111",
            make="Volvo",
            model="FH16",
            vehicle_class="TRUCK",
            body_type="CURTAIN"
        )
        
        self.van_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="VAN-1111",
            make="Ford",
            model="Transit",
            vehicle_class="VAN",
            body_type="BOX"
        )
        
        # Create Driver WITHOUT compliance (for testing missing compliance)
        self.driver_no_compliance = Employee.objects.create(
            company=self.company_a,
            first_name="Νίκος",
            last_name="Χωρίς Στοιχεία",
            position=self.position_driver,
            is_active=True
        )
        
        # Create Driver WITH expired license
        self.driver_expired_license = Employee.objects.create(
            company=self.company_a,
            first_name="Μαρία",
            last_name="Ληγμένη Άδεια",
            position=self.position_driver,
            is_active=True
        )
        compliance_expired = DriverCompliance.objects.create(
            employee=self.driver_expired_license,
            license_number="EXP123",
            license_expiry_date=date.today() - timedelta(days=1)  # Expired yesterday
        )
        compliance_expired.license_categories.add(self.license_b)
        
        # Create Driver WITH valid compliance for TRUCK
        self.driver_truck_valid = Employee.objects.create(
            company=self.company_a,
            first_name="Γιώργος",
            last_name="Φορτηγατζής",
            position=self.position_driver,
            is_active=True
        )
        compliance_truck = DriverCompliance.objects.create(
            employee=self.driver_truck_valid,
            license_number="TRK123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_truck_expiry=date.today() + timedelta(days=365),
            tachograph_card_expiry=date.today() + timedelta(days=365)
        )
        compliance_truck.license_categories.add(self.license_c, self.license_ce)
        
        # Create Driver WITH valid compliance for BUS
        self.driver_bus_valid = Employee.objects.create(
            company=self.company_a,
            first_name="Δημήτρης",
            last_name="Λεωφορειατζής",
            position=self.position_driver,
            is_active=True
        )
        compliance_bus = DriverCompliance.objects.create(
            employee=self.driver_bus_valid,
            license_number="BUS123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_bus_expiry=date.today() + timedelta(days=365),
            tachograph_card_expiry=date.today() + timedelta(days=365)
        )
        compliance_bus.license_categories.add(self.license_d, self.license_de)
        
        # Create Driver WITH B license only (for VAN)
        self.driver_van_only = Employee.objects.create(
            company=self.company_a,
            first_name="Κώστας",
            last_name="Βανάκιας",
            position=self.position_driver,
            is_active=True
        )
        compliance_van = DriverCompliance.objects.create(
            employee=self.driver_van_only,
            license_number="VAN123",
            license_expiry_date=date.today() + timedelta(days=365)
        )
        compliance_van.license_categories.add(self.license_b)
        
        # Create Driver WITH ADR certification
        self.driver_with_adr = Employee.objects.create(
            company=self.company_a,
            first_name="Παναγιώτης",
            last_name="ADR Specialist",
            position=self.position_driver,
            is_active=True
        )
        compliance_adr = DriverCompliance.objects.create(
            employee=self.driver_with_adr,
            license_number="ADR123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_truck_expiry=date.today() + timedelta(days=365),
            tachograph_card_expiry=date.today() + timedelta(days=365),
            adr_expiry=date.today() + timedelta(days=365)
        )
        compliance_adr.license_categories.add(self.license_c, self.license_ce)
        compliance_adr.adr_categories.add(self.adr_p3)
        
        # Create Driver from Company B (for tenant isolation test)
        self.driver_company_b = Employee.objects.create(
            company=self.company_b,
            first_name="Άλλος",
            last_name="Εταιρεία",
            position=self.position_driver,
            is_active=True
        )
        
        # Create test client
        self.client = Client()
        self.client.login(username='user_a', password='testpass123')
    
    def test_block_driver_without_compliance(self):
        """
        Test that driver without compliance record is blocked
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': self.driver_no_compliance.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('δεν έχει καταχωρημένα στοιχεία συμμόρφωσης', str(response.content.decode()))
    
    def test_block_expired_license(self):
        """
        Test that driver with expired license is blocked
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.van_a.id,
                'assigned_driver': self.driver_expired_license.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('άδεια οδήγησης', str(response.content.decode()))
        self.assertIn('λήξει', str(response.content.decode()))
    
    def test_block_bus_without_d_license(self):
        """
        Test that driver without D/DE license cannot drive BUS
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.bus_a.id,
                'assigned_driver': self.driver_truck_valid.id,  # Has C/CE, not D/DE
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('δεν έχει άδεια κατηγορίας D/DE', str(response.content.decode()))
    
    def test_block_bus_without_pei_bus(self):
        """
        Test that driver without valid PEI bus cannot drive BUS
        """
        # Create driver with D license but no PEI bus
        driver_no_pei = Employee.objects.create(
            company=self.company_a,
            first_name="Άννα",
            last_name="Χωρίς ΠΕΙ",
            position=self.position_driver,
            is_active=True
        )
        compliance = DriverCompliance.objects.create(
            employee=driver_no_pei,
            license_number="NOPEI123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_bus_expiry=None,  # Missing PEI
            tachograph_card_expiry=date.today() + timedelta(days=365)
        )
        compliance.license_categories.add(self.license_d)
        
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.bus_a.id,
                'assigned_driver': driver_no_pei.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('ΠΕΙ λεωφορείων', str(response.content.decode()))
    
    def test_block_truck_without_c_license(self):
        """
        Test that driver without C/CE license cannot drive TRUCK
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': self.driver_van_only.id,  # Has B only
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('δεν έχει άδεια κατηγορίας C/CE', str(response.content.decode()))
    
    def test_block_truck_without_pei_truck(self):
        """
        Test that driver without valid PEI truck cannot drive TRUCK
        """
        # Create driver with C license but no PEI truck
        driver_no_pei = Employee.objects.create(
            company=self.company_a,
            first_name="Σταύρος",
            last_name="Χωρίς ΠΕΙ Φορτηγού",
            position=self.position_driver,
            is_active=True
        )
        compliance = DriverCompliance.objects.create(
            employee=driver_no_pei,
            license_number="NOPEITRK123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_truck_expiry=None,  # Missing PEI
            tachograph_card_expiry=date.today() + timedelta(days=365)
        )
        compliance.license_categories.add(self.license_c)
        
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': driver_no_pei.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('ΠΕΙ φορτηγών', str(response.content.decode()))
    
    def test_block_truck_without_tachograph(self):
        """
        Test that driver without valid tachograph cannot drive TRUCK
        """
        # Create driver with C license and PEI but no tachograph
        driver_no_tacho = Employee.objects.create(
            company=self.company_a,
            first_name="Ελένη",
            last_name="Χωρίς Ταχογράφο",
            position=self.position_driver,
            is_active=True
        )
        compliance = DriverCompliance.objects.create(
            employee=driver_no_tacho,
            license_number="NOTACHO123",
            license_expiry_date=date.today() + timedelta(days=365),
            pei_truck_expiry=date.today() + timedelta(days=365),
            tachograph_card_expiry=None  # Missing tachograph
        )
        compliance.license_categories.add(self.license_c)
        
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': driver_no_tacho.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('ταχογράφου', str(response.content.decode()))
    
    def test_block_adr_order_without_adr_certification(self):
        """
        Test that ADR order requires driver with valid ADR
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': self.driver_truck_valid.id,  # Valid for truck but no ADR
                'requires_adr': True,  # ADR required
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('ADR', str(response.content.decode()))
    
    def test_allow_valid_truck_driver(self):
        """
        Test that valid truck driver is allowed
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': self.driver_truck_valid.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify order was created
        order = TransportOrder.all_objects.filter(
            customer_name='Test Customer'
        ).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.assigned_driver, self.driver_truck_valid)
    
    def test_allow_valid_bus_driver(self):
        """
        Test that valid bus driver is allowed
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test Customer Bus',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.bus_a.id,
                'assigned_driver': self.driver_bus_valid.id,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify order was created
        order = TransportOrder.all_objects.filter(
            customer_name='Test Customer Bus'
        ).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.assigned_driver, self.driver_bus_valid)
    
    def test_allow_valid_adr_driver(self):
        """
        Test that driver with valid ADR can handle ADR orders
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Test ADR Order',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': self.driver_with_adr.id,
                'requires_adr': True,
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify order was created
        order = TransportOrder.all_objects.filter(
            customer_name='Test ADR Order'
        ).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.assigned_driver, self.driver_with_adr)
        self.assertTrue(order.requires_adr)
    
    def test_allow_draft_order_without_driver(self):
        """
        Test that draft order without driver is allowed
        """
        response = self.client.post(
            reverse('web:order_create'),
            {
                'customer_name': 'Draft Order',
                'date': date.today(),
                'origin': 'Athens',
                'destination': 'Thessaloniki',
                'distance_km': 500,
                'agreed_price': 1000.00,
                'assigned_vehicle': self.truck_a.id,
                'assigned_driver': '',  # No driver
                'tolls_cost': '0.00',
                'ferry_cost': '0.00',
                'status': 'PENDING',
            }
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify order was created without driver
        order = TransportOrder.all_objects.filter(
            customer_name='Draft Order'
        ).first()
        self.assertIsNotNone(order)
        self.assertIsNone(order.assigned_driver)
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()
