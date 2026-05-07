demo:
	python3 -m malaysia_fsi.demo run --bank maybank-valid.csv --invoices invoices-exact-match/ --receipts receipts/ --output demo-report

web-demo:
	python3 -m malaysia_fsi.web_demo.app

verify:
	python3 -m pytest -v
	python3 scripts/validate_malaysia_phase1.py
	python3 scripts/verify_malaysia_fsi.py
