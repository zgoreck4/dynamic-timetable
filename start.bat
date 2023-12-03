@echo off
setlocal enabledelayedexpansion
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register scheduler localhost scheduler)
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register passenger localhost passenger)
for /f "delims=" %%i in ('docker compose ps -q') do (set "container_id=%%i" && docker exec -it !container_id! prosodyctl register routing_bus localhost routing_bus)
