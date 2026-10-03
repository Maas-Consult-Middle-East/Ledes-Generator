### Ledes

This is an app for Ledes text generating in Frappe

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app ledes
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/ledes
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
# Ledes
# Ledes-Generator
# Ledes-Generator

### LEDES export configuration

After updating the app, run `bench --site <site> migrate` to install the custom
fields and the single **LEDES Settings** DocType.

- Customer: set **LEDES Client ID** (`custom_ledes_client_id`).
- Company: set **LEDES Law Firm ID** (`custom_ledes_law_firm_id`).
- Employee linked to the Sales Invoice creator: set **Timekeeper Classification**
  (`custom_timekeeper_classification`) alongside the existing Timekeeper ID.
- LEDES Settings: configure **Default Invoice Description**, **VAT Expense Code**,
  and **VAT Description**. Their initial defaults are `final`, `E125`, and
  `Foreign VAT Charges`; exports read these settings instead of fixed strings.
- Sales Invoice Item: optionally set **LEDES Type** and **LEDES Adjustment Amount**.
  An empty type is inferred as `E` when an expense code exists, otherwise `F`.
  An empty adjustment amount exports as zero.

No Customer, Company, or Employee IDs/classifications are automatically populated.
Set the appropriate values on each record before exporting. The former fixed values
were client ID `589`, law firm ID `A00000856`, and classification `OT`.

Existing matter mappings remain Sales Invoice `custom_our_reference` and
`custom_your_financial_ref`. The latter is required at export time. Missing client
ID, law firm ID, classification, VAT configuration, or line description also blocks
export with a configuration message. Lines without an expense code require Item
Task Code and Activity Code. Placeholder strings are no longer exported.
Invoice descriptions still prefer the invoice's LEDES description, then remarks,
then the configured default. The VAT row retains type `E`, quantity `1.00`, zero
adjustment, and blank task/activity codes.

Run standalone export regression tests with:

```bash
python3 -m unittest discover -s apps/ledes/tests -v
```
