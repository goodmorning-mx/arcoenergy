# ArcoEnergy DEV mock data

`backend/app/seed_dev_mock_data.py` provides a repeatable preview dataset for the CRM and field PWA. All generated records are fictional and carry a `DEMO` name, folio, note, or creator marker. The script uses stable IDs, updates only its own fixture records, and never deletes rows. Existing quote packages and standard chart-of-account codes are reused without rewriting their metadata.

After the code is deployed to the **DEV API only**, run inside the ArcoEnergy DEV API container:

```sh
python -m app.seed_dev_mock_data --apply
```

The script refuses to run unless `APP_ENV` is `dev` or `development`; without `--apply`, it performs no writes. Rerunning it refreshes the deterministic DEMO fixtures rather than creating duplicates.

The preview covers customers and follow-ups; quote packages and quotes; projects, sales, installations, installer assignments and work-order materials; inventory categories, products, purchases, receipts and consumption; suppliers and payments; receivables and customer payments; cash/bank accounts and movements; project expenses and profitability adjustments; and balanced ledger entries for the balance sheet, income statement, and cash-flow views.

It deliberately does not manufacture history-card evidence, authentication identities, push subscriptions, agent action intents, offline operation receipts, financial corrections, or backup/snapshot runs. Those records represent real stakeholder evidence, security state, idempotency receipts, corrections, or completed operational events and must only be created by their real workflows.
