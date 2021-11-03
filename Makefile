SHELL := /bin/bash

test:
	pytest

build:
	docker build -t wagmi -f DockerFile .

run:
	docker run --name wagmi -p 8080:8080 -d --link postgres wagmi

runpg:
	docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d postgres:12

createdb:
	createdb -h localhost -O postgres -U postgres wagmi

clean:
	@rm -rf build dist docs-build *.egg-info
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	@find . -type d -name .pytest_cache -delete

.PHONY: help Makefile
