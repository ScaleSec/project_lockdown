SHELL := /usr/bin/env bash

APP_NAME := lockdown
TAG ?= latest
PROJECT_ID ?= "test"

.PHONY: all

all: build

build: 
	docker build -t $(APP_NAME):$(TAG) .

run:
	docker run -it "$(APP_NAME):$(TAG)" bash
	
dev-build:
	docker build -t $(APP_NAME):dev .

test: dev-build
	docker run -it -v $(PWD)/pip_cache:/app/pip_cache "$(APP_NAME):dev"

push:
	docker tag $(APP_NAME):$(TAG) gcr.io/$(PROJECT_ID)/$(APP_NAME):$(TAG)
	docker push gcr.io/$(PROJECT_ID)/$(APP_NAME):$(TAG)
