:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Sample script for running SPECjbb2015 in Composite mode.
:: 
:: This sample script demonstrates launching the Controller, TxInjector and 
:: Backend in a single JVM.
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

@echo off

:: Launch command: java [options] -jar specjbb2015.jar -m COMPOSITE [argument] [value] ...

:: Benchmark options (-Dproperty=value to override the default and property file value)
:: Please add -Dspecjbb.controller.host=$CTRL_IP (this host IP) and -Dspecjbb.time.server=true
:: when launching Composite mode in virtual environment with Time Server located on the native host.
set SPEC_OPTS=

:: Java options for Composite JVM
set JAVA_OPTS=

:: Optional arguments for the Composite mode (-l <num>, -p <file>, -skipReport, etc.)
set MODE_ARGS=

:: Number of successive runs
set NUM_OF_RUNS=1

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: This benchmark requires a JDK7 compliant Java VM.  If such a JVM is not on
:: your path already you must set the JAVA environment variable to point to
:: where the 'java' executable can be found.
::
:: If you are using a JDK9 Java VM, see the FAQ at:
::                       http://spec.org/jbb2015/docs/faq.html
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

@set JAVA=java.exe

@set JAVAPATH=
@for %%J in (%JAVA%) do (@set JAVAPATH=%%~$PATH:J)

@if not defined JAVAPATH (
   echo ERROR: Could not find a 'java' executable. Please set the JAVA environment variable or update the PATH.
   exit /b 1
) else (
   @set JAVA="%JAVAPATH%"
)

set counter=1
:LOOP

:: Create result directory
set timestamp=%DATE:~12,2%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set result=%timestamp: =0%
mkdir %result%\config

:: Copy current config to the result directory
copy config %result%\config >nul

cd %result%

echo Run %counter%: %result%
echo Launching SPECjbb2015 in Composite mode...
echo.

echo Start Composite JVM
echo Please monitor %result%\composite.out for progress
@echo on
%JAVA% %SPEC_OPTS% %JAVA_OPTS% -jar ..\specjbb2015.jar -m COMPOSITE %MODE_ARGS% 2>composite.log > composite.out
@echo off

echo.
echo Composite JVM has stopped
echo SPECjbb2015 has finished
echo.

cd ..

IF %counter% == %NUM_OF_RUNS% GOTO END
set /a counter=%counter + 1
GOTO LOOP
:END

exit /b 0
