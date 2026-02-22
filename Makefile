# Makefile 所在目录（项目根目录），保证从任意位置调用 make 时路径正确
ROOT := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
ROOT := $(patsubst %/,%,$(ROOT))

ACCESS ?= ohyee
DOCKER_IMAGE ?= "cap-demo-public-registry.cn-hangzhou.cr.aliyuncs.com/cap-app/agentrun-demo:buy-me-a-coffee-${shell date -u +'%y%m%d-%H%M%S'}" 
LATEST_IMAGE ?= ${shell docker images | awk '/cn-hangzhou/ && /agentrun-demo/ &&/buy-me-a-coffee/ { printf "%s:%s\n", $$1, $$2 }'  | sed -n 1p}
FRONTEND_SOURCES ?= $(shell find frontend -type f -not -path "*/node_modules/*" -not -path "*/dist/*")


.PHONY: help
help: ## 帮助文件
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {sub("\\\\n",sprintf("\n%22c"," "), $$2);printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: setup-nodejs
setup-nodejs:
	cd $(ROOT)/frontend && npm install

setup-python:
	cd $(ROOT)/backend && uv sync 2>/dev/null || (cd $(ROOT)/backend && uv venv --clear && uv pip install -r requirements.txt)

.PHONY: setup
setup: setup-nodejs setup-python ## 初始化开发环境（安装前后端依赖）

.PHONY: dev
dev: ## 一键启动本地开发环境（3 个后端服务 + 前端），Ctrl+C 停止所有服务
	@echo "🚀 启动本地开发环境（统一部署模式）..."
	@echo "   ☕ Coffee API    → http://localhost:8001"
	@echo "   🛵 Delivery API  → http://localhost:8002"
	@echo "   🌐 Gateway       → http://localhost:8000"
	@echo "   💻 Frontend      → http://localhost:5173"
	@echo ""
	@trap 'echo ""; echo "🛑 正在停止所有服务..."; kill 0; exit 0' INT TERM; \
	cd backend && uv run python -m coffee.main & \
	cd backend && uv run python -m delivery.main & \
	sleep 2 && cd backend && uv run python -m gateway.main & \
	cd frontend && npm run dev & \
	wait

.PHONY: dev-backend
dev-backend: ## 仅启动后端服务（Coffee API + Delivery API + Gateway）
	@echo "🚀 启动后端服务..."
	@trap 'echo ""; echo "🛑 正在停止所有服务..."; kill 0; exit 0' INT TERM; \
	cd backend && uv run python -m coffee.main & \
	cd backend && uv run python -m delivery.main & \
	sleep 2 && cd backend && uv run python -m gateway.main & \
	wait

.PHONY: dev-frontend
dev-frontend: ## 仅启动前端开发服务器（Vite，自动代理到 localhost:8000）
	cd frontend && npm run dev

frontend/dist/index.cjs: $(FRONTEND_SOURCES)
	cd frontend && \
	npm run build && \
	cp index.js dist/index.cjs


.PHONY: web
web: frontend/dist/index.cjs ## 调试 - 启动 web 服务器（生产构建版）
	@cd frontend/dist && \
	ENDPOINT=http://localhost:8000 \
	node index.cjs

.PHONY: gateway-agent
gateway-agent: ## 调试 - 单独启动 Gateway Agent（端口 8000）
	COFFEE_API_URL=http://localhost:8001 \
	DELIVERY_API_URL=http://localhost:8002 \
	cd backend && uv run python -m gateway.main

.PHONY: coffee-agent
coffee-agent: ## 调试 - 单独启动 Coffee A2A Agent（端口 8003，分布式模式用）
	cd backend && uv run python -m coffee.a2a

.PHONY: delivery-agent
delivery-agent: ## 调试 - 单独启动 Delivery A2A Agent（端口 8004，分布式模式用）
	cd backend && uv run python -m delivery.a2a

.PHONY: coffee-api
coffee-api: ## 调试 - 单独启动 Coffee API 服务（端口 8001）
	cd backend && uv run python -m coffee.main

.PHONY: delivery-api
delivery-api: ## 调试 - 单独启动 Delivery API 服务（端口 8002）
	cd backend && uv run python -m delivery.main

.PHONY: clean-db
clean-db: ## 清理数据库文件（重新初始化 schema）
	rm -f data/coffee.db data/delivery.db
	@echo "✅ 数据库已清理，下次启动时会自动重建"


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

registry: prepare-registry prepare-frontend # prewarm ## 发布到 Serverless Devs
	s registry publish

