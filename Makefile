ACCESS ?= ohyee
DOCKER_IMAGE ?= "cap-demo-public-registry.cn-hangzhou.cr.aliyuncs.com/cap-app/agentrun-demo:buy-me-a-coffee-${shell date -u +'%y%m%d-%H%M%S'}" 
LATEST_IMAGE ?= ${shell docker images | awk '/cn-hangzhou/ && /agentrun-demo/ &&/buy-me-a-coffee/ { printf "%s:%s\n", $$1, $$2 }'  | sed -n 1p}
FRONTEND_SOURCES ?= $(shell find frontend -type f -not -path "*/node_modules/*" -not -path "*/dist/*")


.PHONY: help
help: ## 帮助文件
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {sub("\\\\n",sprintf("\n%22c"," "), $$2);printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: setup-nodejs
setup-nodejs:
	cd frontend npm install --prefix frontend

setup-python:
	uv venv --clear
	uv pip install -r backend/requirements.txt

.PHONY: setup
setup: setup-nodejs setup-python ## 初始化开发环境


frontend/dist/index.cjs: $(FRONTEND_SOURCES)
	cd frontend && \
	npm run build && \
	cp index.js dist/index.cjs


.PHONY: web
web: frontend/dist/index.cjs ## 调试 - 启动 web 服务器
	@cd frontend/dist && \
	ENDPOINT=http://localhost:8000 \
	node index.cjs

.PHONY: gateway-agent
gateway-agent: ## 调试 - 启动主 Agent
	A2A_URLS=http://localhost:8003,http://localhost:8004 \
	COFFEE_API_URL=http://localhost:8001 \
	DELIVERY_API_URL=http://localhost:8002 \
	uv run -m backend.gateway.main

.PHONY: coffee-agent
coffee-agent: ## 调试 - 启动 Coffee Agent
	COFFEE_TOOLSET_NAME=xixi-coffee-api \
	uv run -m backend.coffee.a2a

.PHONY: delivery-agent
delivery-agent: ## 调试 - 启动 Delivery Agent
	DELIVERY_TOOLSET_NAME=delivery-api \
	uv run -m backend.delivery.a2a

.PHONY: coffee-api
coffee-api: ## 调试 - 启动 Coffee API 服务
	uv run -m backend.coffee.main

.PHONY: delivery-api
delivery-api: ## 调试 - 启动 Delivery API 服务
	uv run -m backend.delivery.main


s_test.yaml: s.yaml
	cat s.yaml \
	| sed 's/{{ *region *}}/cn-hangzhou/g' \
	| sed 's/{{ *agentRuntimeName *}}/buy-me-a-coffee/g' \
	| sed 's/{{ *role *}}/acs:ram::$${config("AccountID")}:role\/buy-me-a-coffee/g' \
	| sed 's/{{ *modelServiceName *}}/model-68sWBa/g' \
	| sed 's/{{ *modelName *}}/qwen3-max/g' \
	> s_test.yaml

.PHONY: deploy
deploy: s_test.yaml push ## 部署到测试环境
	s deploy -a ${ACCESS} -y --skip-push --debug -t s_test.yaml


.PHONY: build
build: ## 构建 Docker 镜像
	docker build --platform linux/amd64 \
		-t ${DOCKER_IMAGE} backend

.PHONY:image
image: ## 显示最新构建的镜像
	@echo ${LATEST_IMAGE} 

.PHONY: docker-build-push
push: ## 推送最新构建的镜像到远程仓库
	docker push ${LATEST_IMAGE}
	
.PHONY: push-all
push-all: push ## 推送镜像到所有 region
	@for region in cn-shanghai cn-beijing cn-shenzhen; do \
		image=$$(echo ${LATEST_IMAGE} | sed  "s/cn-hangzhou/$${region}/"); \
		docker tag ${LATEST_IMAGE} $$image; \
		docker push $$image; \
	done

.PHONY: prewarm
prewarm: push
	IMAGE=${LATEST_IMAGE} bash ./prewarm.sh

src/README.md: README.md
	@mkdir -p src
	@cp README.md src/README.md

src/s.yaml: s.yaml
	@mkdir -p src
	@cp s.yaml src/s.yaml

src/coffee.yaml: coffee.yaml
	@mkdir -p src
	@cp coffee.yaml src/coffee.yaml

src/delivery.yaml: delivery.yaml
	@mkdir -p src
	@cp delivery.yaml src/delivery.yaml

src/frontend/dist/index.cjs: frontend/dist/index.cjs
	@mkdir -p src/frontend
	@find frontend -type f ! -path *node_modules* | xargs -I {} bash -c "mkdir -p \$$(dirname src/{}) && cp {} src/{}"
	

src/backend: backend/**/*
	@mkdir -p src/backend
	@cp -r backend/ src/backend

.PHONY: prepare-registry
prepare-registry: src/README.md src/s.yaml src/coffee.yaml src/delivery.yaml 

.PHONY: prepare-frontend
prepare-frontend: src/frontend/dist/index.cjs

.PHONY: prepare-backend
prepare-backend: src/backend

registry: prepare-registry prepare-frontend ## 发布到 Serverless Devs
	s registry publish

