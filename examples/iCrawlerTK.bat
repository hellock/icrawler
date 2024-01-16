@d:
@cd %~dp0

if exist images (
	echo images folder exists
) ELSE (
	python iCrawlerTK.py 1> iCrawlerTK.log 2> iCrawlerTKErrors.log
)

pause
