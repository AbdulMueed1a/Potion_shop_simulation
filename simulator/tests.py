from unittest.mock import patch
from django.test import SimpleTestCase, Client
from . import configuration
from .forms import ExperimentForm
from .configuration import defaults, initial
from simulate import stock_options


class WebTests(SimpleTestCase):
    def test_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        for text in ['How much will you brew today?', '<table', 'name="demand_0"', 'form="experiment-form"', 'Maximum stock']:
            self.assertContains(response, text)
        for text in ['<textarea', 'editable JSON', 'Download evidence']:
            self.assertNotContains(response, text)

    def test_changed_price(self):
        config = defaults(); config['selling_price'] = 80
        response = self.client.post('/', initial(config))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['best'], '80')

    def test_invalid_price(self):
        config = defaults(); config['selling_price'] = 1
        self.assertEqual(self.client.post('/', initial(config)).status_code, 400)

    def test_invalid_probability(self):
        config = defaults(); config['day_type_percent'] = [30, 40, 20]
        self.assertEqual(self.client.post('/', initial(config)).status_code, 400)
        for field, value in [('chance_0_0', 4), ('chance_0_0', 101), ('chance_1_1', -1), ('demand_0', 50), ('day_name_0', 'Normal')]:
            with self.subTest(field=field, value=value):
                data = initial(defaults()); data[field] = value
                self.assertEqual(self.client.post('/', data).status_code, 400)
        data = initial(defaults()); del data['chance_0_0']
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('chance_0_0', response.context['form'].errors)

    def test_csrf(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post('/', initial(defaults())).status_code, 403)

    def test_result_tables(self):
        data = initial(defaults()); data['chosen_stock'] = 40
        page = self.client.post('/', data)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Daily calculation audit')
        self.assertEqual(len(page.context['summary_rows']), 11)
        self.assertEqual(len(page.context['run_rows']), 30)
        self.assertTrue(all(row['stock'] == 40 for row in page.context['run_rows']))
        audit = page.context['audit_rows'][0]
        self.assertEqual((audit['stock'], audit['demand'], audit['cash_profit'], audit['textbook_score']), (40, 70, 800, 200))
        self.assertEqual(len(page.context['trace_page']), 100)
        self.assertEqual(self.client.post('/download/', data).status_code, 404)
        # Pagination retains the exact input model and selected range.
        config = defaults()
        config.update(day_types=['Active', 'Normal', 'Quiet'], demand_values=[30, 50, 60, 70, 80, 90, 100],
                      day_type_percent=[40, 40, 20], selling_price=80, stock_min=20, stock_max=500)
        config['demand_percent_by_type'][0] = [4, 4, 15, 20, 35, 15, 7]
        data = initial(config); data['chosen_stock'] = 40
        page = self.client.post('/', data)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context['form'].cleaned_data['config'], config)
        second = self.client.post('/', {**page.context['view_values'], 'trace_page': '2'})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.context['selected'], 40)
        self.assertEqual(second.context['form'].cleaned_data['config'], config)
        self.assertEqual(second.context['trace_page'].number, 2)
        self.assertEqual(second.context['trace_page'][0], page.context['result'][2][100])
        self.assertContains(second, 'Page 2 of 300')
        self.assertTrue(second.context['trace_requested'])

    def test_user_selects_stock(self):
        data = initial(defaults()); data['chosen_stock'] = 40
        page = self.client.post('/', data)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context['selected'], 40)
        self.assertEqual(page.context['best'], '70')
        # User-controlled bounds, including quantities above demand support.
        for lower, upper, step, selected in [(0, 500, 10, 500), (500, 500, 1, 500), (5, 505, 25, 505), (0, 1000000, 100000, 1000000)]:
            with self.subTest(lower=lower, upper=upper, step=step):
                data = initial(defaults())
                data.update(stock_min=lower, stock_max=upper, bundle_size=step, chosen_stock=selected, runs=2, days_per_run=20)
                page = self.client.post('/', data)
                self.assertEqual(page.status_code, 200)
                self.assertEqual([row['stock'] for row in page.context['summary_rows']], list(range(lower, upper + 1, step)))
                self.assertEqual(page.context['selected'], selected)
                self.assertTrue(all(row['stock'] == selected for row in page.context['audit_rows']))
        for changes in [dict(stock_min=100, stock_max=50), dict(bundle_size=0), dict(stock_max=50),
                        dict(stock_max=10**12), dict(stock_max=500, bundle_size=1)]:
            data = initial(defaults()); data.update(changes)
            with self.subTest(changes=changes):
                self.assertEqual(self.client.post('/', data).status_code, 400)
        # Changed file defaults still select a feasible starting stock.
        for batch, preference in [(20, 70), (30, 70), (10, 500)]:
            config = defaults(); config.update(bundle_size=batch, default_stock=preference)
            with self.subTest(batch=batch), patch.object(configuration, 'defaults', return_value=config):
                response = self.client.get('/')
                self.assertEqual(response.status_code, 200)
                self.assertIn(response.context['selected'], stock_options(config))
                self.assertEqual(response.context['form']['chosen_stock'].value(), response.context['selected'])
                self.assertEqual(ExperimentForm().fields['chosen_stock'].initial, response.context['selected'])
