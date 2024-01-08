# This is a simple webcrawler demo
import requests
import re

class WebCrawler():

    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "prompt": ("list[str]",)}}
    
    RETURN_TYPES = {"response":{"prompt":("str")}}

    FUNCTION = "crawler"

    TEMPLATE_PROMPT:str = """Based on user's inputs, 
     summarizes the query keywords in the following format,
     <keywords>the keywords for web crawlers </keywords>
     to obtain more information through online web crawlers.
     For example: <keywords> Nvidia RTX Graghic Card</keywords>
     After that, system will return the information obtained on the searching.
     Please complete the answer to the user based on those information."""

    EXTRA_STOP_TOKEN:str = "</keywords>"

    START_TOKEN:str = "<keywords>"

    session:requests.Session
    title_pattern:re.Pattern
    brief_pattern:re.Pattern
    link_pattern:re.Pattern
    detail_pattern:re.Pattern
    search_engine:str
    headers:dict
    proxies:dict

    def __init__(self,
                 title_pattern:re.Pattern = re.compile('<a.target=..blank..target..(.*?)</a>'),
                 brief_pattern:re.Pattern = re.compile('K=.SERP(.*?)</p>'),
                 link_pattern:re.Pattern = re.compile('(?<=(a.target=._blank..target=._blank..href=.))(.*?)(?=(..h=))') ,
                 detail_pattern:re.Pattern = re.compile('>(.*?)<'),
                 search_engine:str = 'https://www.bing.com/search?q={}',
                 headers:dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36 Edg/120.0.2210.77'},
                 proxies:dict =  {"http": None,"https": None,}
                 ) -> None:
        self.session = requests.Session()
        self.title_pattern = title_pattern
        self.brief_pattern = brief_pattern
        self.link_pattern = link_pattern
        self.detail_pattern = detail_pattern

        self.search_engine = search_engine
        self.headers = headers
        self.proxies = proxies

    def crawler(self,prompt:list[str],count = 4) -> dict:
        if len(prompt) == 0:
            return {"prompt":"no search result"} 
        search_query:str = prompt.pop()
        for tmp in reversed(prompt):
            search_query =  tmp + '+' + search_query     
        try:
            url = self.search_engine.format(search_query)
            res = self.session.get(url, headers=self.headers, proxies=self.proxies)
            r = res.text

            title = self.title_pattern.findall(r)
            brief = self.brief_pattern.findall(r)
            link = self.link_pattern.findall(r)

            if len(title) == 0:
                return self.crawler(prompt=prompt)

            clear_brief = []
            for i in brief:
                tmp = re.sub('<[^<]+?>', '', i).replace('\n', '').strip()
                tmp1 = re.sub('^.*&ensp;', '', tmp).replace('\n', '').strip()
                tmp2 = re.sub('^.*>', '', tmp1).replace('\n', '').strip()
                clear_brief.append(tmp2)

            clear_title = []
            for i in title:
                tmp = re.sub('^.*?>', '', i).replace('\n', '').strip()
                tmp2 = re.sub('<[^<]+?>', '', tmp).replace('\n', '').strip()
                clear_title.append(tmp2)

            res =  [{'title': "["+clear_title[i]+"]("+link[i][1]+")", 'content':clear_brief[i]}
                    for i in range(min(count, len(brief)))]
            return {"prompt":str(res)}
        except:
            return {"prompt":"no search result"}
    
    def get_detail(self,site:str) -> dict:
        result:dict = {}
        try:
            res = self.session.get(site, headers=self.headers, proxies=self.proxies)
            r = res.text
            # Data preparation
            r = r.replace('\n','').strip()
            r = r.replace('\r','').strip()
            r = r.replace('\s','').strip()
            r = re.sub('script(.*?)</','',r).replace('\n', '').strip()
            r = re.sub('style(.*?)</','',r).replace('\n', '').strip()
            r = re.sub('link(.*?)</','',r).replace('\n', '').strip()
        
            brief = self.detail_pattern.findall(r)
            brief = [x.strip() for x in brief if x.strip()!='']
            clear_brief = []
            for i in brief:
                tmp = re.sub('<[^<]+?>', '', i).replace('\n', '').strip()
                tmp1 = re.sub('^.*&ensp;', '', tmp).replace('\n', '').strip()
                tmp2 = re.sub('^.*>', '', tmp1).replace('\n', '').strip()
                clear_brief.append(tmp2)
            result['site'] = site
            result['content'] = clear_brief
            return result
        except:
            return result

FUNCTION_CLASS_MAPPINGS = {
    "WEBCRAWLER" : WebCrawler
}
