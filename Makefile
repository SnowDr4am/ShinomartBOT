COMPOSE_FILE ?= docker-compose.yml
SERVICE ?= app
ALEMBIC ?= alembic
m ?= auto

.PHONY: up down logs ps restart stop migrate migrate-down revision history current stamp \
        revision_local migrate_local

# -------- DOCKER --------
up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down -v

logs:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=200

ps:
	docker compose -f $(COMPOSE_FILE) ps

restart:
	docker compose -f $(COMPOSE_FILE) restart

stop:
	docker compose -f $(COMPOSE_FILE) stop

# -------- MIGRATIONS (локально) --------
revision_local: ## создать ревизию локально (make revision_local m="init")
	$(ALEMBIC) revision --autogenerate -m "$(m)"

migrate_local: ## накатить миграции локально
	$(ALEMBIC) upgrade head

migrate: ## создать ревизию и сразу накатить (make migrate m="add wallets")
	$(ALEMBIC) revision --autogenerate -m "$(m)" && $(ALEMBIC) upgrade head