#image_crawler

##Introduction
This python package is a mini framework of image crawlers. 

##Stucture
It consists of 3 main components (Feeder, Parser and Downloader) and 2 FIFO queues (url_queue and task_queue).
 The workflow is as follows.

![workflow](http://7xopqn.com1.z0.glb.clouddn.com/workflow.png)

* `url_queue` stores the url of pages which may contain images
* `task_queue` stores the image url as well as any meta data you like, each element in the queue is a dictionary and must contain the field `img_url`
* Feeder puts page urls to `url_queue`
* Parse request and parse the page, then extract the image urls and puts them into `task_queue`
* Downloader gets task from `task_queue` and request the images, then save them in the given path.

Feeder, parser and downloader all supports multi-thread, you can specify the number of threads they use respectively.

##Basic usage

###Built-in crawlers
The framework has 3 built-in crawlers and all of them are search engine crawlers. They are Google, Bing and Baidu. Here is an example of how to use the built-in crawlers.

```python
from image_crawler.examples import GoogleImageCrawler

google_crawler = GoogleImageCrawler('images/google')
google_crawler.crawl(keyword='sunny', max_num=1000, feeder_thr_num=1,
					 parser_thr_num=1, downloader_thr_num=4)

```
Run this code and the crawler will download the images in the search result page using 1 thread to feed urls, 1 thread to parse the page and 4 threads to download the images.

You can see the complete examples in *test.py*

###Other crawlers
You will have to write your own classes or overwrite some methods. See *examples.py* for example and more infomation will be supplemented
