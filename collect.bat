@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

if "%~1"=="" (
    set /p "ROOT=Введите корневую папку: "
) else (
    set "ROOT=%~1"
)

if not exist "%ROOT%" (
    echo Папка не найдена: %ROOT%
    pause
    exit /b 1
)

set "OUTPUT=%CD%\project_code.txt"
set "EXTS=.py .js .ts .jsx .tsx .html .css .scss .json .md .txt .java .c .cpp .h .hpp .cs .go .rs .php .rb .sql .yml .yaml .xml .sh .bat .cmd .ini .cfg .toml .vue .svelte"

> "%OUTPUT%" echo.

for /r "%ROOT%" %%F in (*) do (
    set "FILE=%%F"
    set "EXT=%%~xF"

    if /I not "%%~nxF"=="project_code.txt" (
        set "SKIP="
        echo !FILE! | findstr /I /C:"\node_modules\\" /C:"\.git\\" /C:"\venv\\" /C:"\.venv\\" /C:"\__pycache__\\" /C:"\dist\\" /C:"\build\\" /C:"\target\\" >nul && set "SKIP=1"

        if not defined SKIP (
            echo !EXTS! | findstr /I /C:"!EXT!" >nul
            if !errorlevel! == 0 (
                echo ============================================================>> "%OUTPUT%"
                echo FILE: %%F>> "%OUTPUT%"
                echo ============================================================>> "%OUTPUT%"
                type "%%F">> "%OUTPUT%"
                echo.>> "%OUTPUT%"
                echo.>> "%OUTPUT%"
                echo [+] %%F
            )
        )
    )
)

echo.
echo Готово! Всё сохранено в: %OUTPUT%
pause