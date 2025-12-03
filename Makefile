
.PHONY: setup-nodejs
setup-nodejs:
	cd frontend npm install --prefix frontend

setup-python:
	uv venv --clear
	uv pip install -r backend/requirements.txt

.PHONY: setup
setup: setup-nodejs setup-python


.PHONY: web
web:
	cd frontend && \
	npm run build && \
	cp index.js dist/index.js && \
	cd dist && \
	ENDPOINT=http://localhost:8000 \
	bun index.js

.PHONY: gateway-agent
gateway-agent:
	A2A_URLS=http://localhost:8003,http://localhost:8004 \
	COFFEE_API_URL=http://localhost:8001 \
	DELIVERY_API_URL=http://localhost:8002 \
	uv run -m backend.gateway.main

.PHONY: coffee-agent
coffee-agent:
	COFFEE_API_URL=http://localhost:8001 \
	uv run -m backend.coffee.a2a

.PHONY: delivery-agent
delivery-agent:
	DELIVERY_API_URL=http://localhost:8002 \
	uv run -m backend.delivery.a2a

.PHONY: coffee-api
coffee-api:
	uv run -m backend.coffee.main

.PHONY: delivery-api
delivery-api:
	uv run -m backend.delivery.main

ACCESS=ohyee

.PHONY: deps
deps:
	s build -a ${ACCESS}

.PHONY: deploy
deploy:
	s deploy -a ${ACCESS} -y