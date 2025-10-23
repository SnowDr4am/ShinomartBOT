# --- Settings ---
COMPOSE_FILE ?= docker-compose.yml

# --- Targets ---
up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down -v

ps:
	docker compose -f $(COMPOSE_FILE) ps

stop:
	docker compose -f $(COMPOSE_FILE) stop

restart:
	docker compose -f $(COMPOSE_FILE) restart