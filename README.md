# Family Finance Tracker — 3-tier application

**Presentation:** React + Vite + Nginx | **Application:** Python Flask REST API + SQLAlchemy | **Database:** MySQL 8.0

Tracks Farming, Cow Milk Business, Poultry Business and Tushar's Salary. All transaction amounts are INR. Reports use the Indian financial year (1 April–31 March). There is no exchange-rate table.

## Features
- Login with an initial administrator account configured in `.env`
- Dashboard with family income, expenses and net balance
- Business-wise income, expenses and net balance
- Monthly income/expense chart and annual source comparison
- Add income and expense transactions
- Filter and delete transactions
- Persistent MySQL volume

## Run
1. Install Docker Engine and Docker Compose v2.
2. Copy `.env.example` to `.env` and replace every placeholder with unique, strong secrets.
3. Start: `docker compose up -d --build`
4. Check: `docker compose ps` and `docker compose logs -f backend`
5. Open `http://YOUR_SERVER_PUBLIC_IP/` (port 80).
6. Sign in using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`.

For EC2 testing, allow inbound TCP 80 from your own public IP in the instance security group. Do not publish MySQL port 3306. Configure HTTPS and a domain before entering real family financial information.

## Database
Tables: `users`, `businesses`, `categories`, `income`, `expenses`. Tables and starter businesses/categories are created automatically.

Inspect MySQL:
```
docker compose exec db mysql -u family_user -p family_finance
SHOW TABLES;
SELECT * FROM businesses;
SELECT * FROM income ORDER BY transaction_date DESC;
SELECT * FROM expenses ORDER BY transaction_date DESC;
```

## Backup
```
docker compose exec -T db sh -c 'exec mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" family_finance' > family_finance_backup.sql
```
Keep backups securely off the EC2 instance and test restores.

## Security and scope
- Starter release includes one seeded administrator login. Public registration is disabled. Family account administration, roles, password reset, audit history and editing transactions are not included yet.
- Change all secrets before deployment. The admin is seeded only when the users table is empty; changing `.env` later will not update an existing account's password.
- Do not expose MySQL 3306 publicly. Restrict port 80 during testing; configure HTTPS before production use.
- Figures are management summaries, not audited accounts or tax advice. Salary is income; net family balance is all recorded income minus all recorded expenses.
- Amounts are INR. No JPY conversion or exchange-rate storage is implemented.
- CI/CD Pipeline: Automated deployment using Jenkins, Docker Hub, and AWS EC2.
