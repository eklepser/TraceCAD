@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "OUTPUT=project_code.txt"
set "ROOT=%~dp0"

:: Очистить/создать выходной файл
> "%OUTPUT%" echo.

:: Расширения файлов, которые нужно собрать (можно расширить)
set "EXTS=.py .js .ts .jsx .tsx .html .css .scss .json .md .txt .java .c .cpp .h .hpp .cs .go .rs .php .rb .sql .yml .yaml .xml .sh .bat .cmd .ini .cfg .toml .vue .svelte"

for /r "%ROOT%" %%F in (*) do (
    set "FILE=%%F"
    set "EXT=%%~xF"

    :: Пропускаем сам выходной файл
    if /I not "%%~nxF"=="%OUTPUT%" (

        :: Пропускаем папки с мусором
        set "SKIP="
        echo !FILE! | findstr /I /C:"\node_modules\\" /C:"\.git\\" /C:"\venv\\" /C:"\.venv\\" /C:"\__pycache__\\" /C:"\dist\\" /C:"\build\\" /C:"\target\\" >nul && set "SKIP=1"

        if not defined SKIP (
            :: Проверяем расширение
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