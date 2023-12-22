@echo off
setlocal enabledelayedexpansion
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register scheduler localhost scheduler)
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register passenger localhost passenger)
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register routing_bus1 localhost routing_bus1)
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register routing_bus2 localhost routing_bus2)
