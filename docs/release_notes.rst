Release notes
=============

0.6.1 (2018-05-25)
------------------

- **New**: Add an option to skip downloading when the file already exists.

0.6.0 (2018-03-17)
------------------

- **New**: Make the api of search engine crawlers (GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler) universal, add the argument ``filters`` and remove arguments ``img_type``, ``img_color``, ``date_min``, etc.
- **New**: Add more search options (type, color, size, layout, date, people, license) for Bing (Thanks `@kirtanp <https://github.com/kirtanp>`_).
- **New**: Add more search options (type, color, size) for Baidu.
- **Fix**: Fix the json parsing error of ``BaiduImageCrawler`` when some invalid escaped characters exist.