@echo off
setlocal
set "MAZ_BUNDLE=%~dp0.."
set "PATH=%MAZ_BUNDLE%\external\nodejs;%MAZ_BUNDLE%\external\codex-dependencies\python;%MAZ_BUNDLE%\external\codex-dependencies\native\poppler\Library\bin;%PATH%"
set "MAZ_NODE_PREVIEW=1"
set "NODE_USE_ENV_PROXY=0"
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
cd /d "%MAZ_BUNDLE%\testcar"
echo Open http://localhost:3000/ after the server starts.
call "%MAZ_BUNDLE%\external\nodejs\npm.cmd" run dev -- --host 127.0.0.1 --port 3000
pause
