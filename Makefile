COMPOSE := docker-compose

ifeq ($(OS),Windows_NT)
	IS_WINDOWS := 1
else
	IS_WINDOWS := 0
endif

## make up — запустить контейнеры (в фоне)
up:
	$(COMPOSE) up -d

## make down — остановить и удалить контейнеры
down:
	$(COMPOSE) down

## make stop — просто остановить контейнеры (без удаления)
stop:
	$(COMPOSE) stop

## make restart — перезапустить контейнеры
restart:
	$(COMPOSE) restart