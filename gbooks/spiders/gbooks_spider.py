import scrapy
from scrapy.http import Request, Response
import json
from gbooks.items import SnippetItem
import re
import string

'''
This is the url format to make a search request for google books
https://books.google.com.br/books
     ?id=ztrj8aph-4sC
     &printsec=frontcover
     &dq=isbn:141290224X
     &hl=pt-BR
     &sa=X
     &ei=IYGYVP-LM5X-sAT41IGgBg
     &ved=0CBQQ6AEwAA
     &jscmd=SearchWithinVolume&q= <<word or phrase to research>>
     &scoring=r
'''
class GBooksSpider(scrapy.Spider):
    name = "gbooks"
    allowed_domains = ["books.google.com", "books.google.com.br"]

    book_id = "ztrj8aph-4sC"
    book_isbn = "141290224X"
    book_ei = "IYGYVP-LM5X-sAT41IGgBg"
    book_ved = "0CBQQ6AEwAA"

    #term = "administration" # the ideia is to grow the search terms
    #term = "experienced"
    terms_new = set() # list of new terms to search
    terms_used = set() # list of used terms already searched 

    def __init__(self):
        #self.terms_new.add("forget")
        #self.terms_new.add("experienced")
        self.terms_new.add("literature")
        self.last_term = ''

    def start_requests(self):
        # generate request url to download the book
        return [self.new_search_request()]
        
    def new_search_request(self):
        # check if there are more terms
        if not self.terms_new: 
            return None
        
        term = self.terms_new.pop()
        self.terms_used.add(term)
        
        self.last_term = term
        
        return Request("https://books.google.com.br/books?id=" + \
                self.book_id + \
                "&printsec=frontcover&dq=isbn:" + \
                self.book_isbn + \
                "&hl=pt-BR&sa=X&ei=" + \
                self.book_ei + \
                "&ved=" + \
                self.book_ved + \
                "&jscmd=SearchWithinVolume&q=" + \
                term + \
                "&scoring=r")

    def parse(self, response):
        # parse the response
        # It should store the phrase and the page
        # It should also expand the numbers of terms to search and return the new search requests
        # It is necessary to espace the \r and \n 
        #body = response.body.replace('\r', '\\r').replace('\n', '\\n')
        #print body
        data = json.loads(response.body_as_unicode())
        
        print ('Search Term:' + self.last_term)
        print ('Number of Results: ' + `data['number_of_results']`)
        
        n_results = data['number_of_results']
        
        if n_results != 0:
            for result in data['search_results']:
                snippet = SnippetItem()
                snippet['page'] = result['page_number']
                snippet['text'] = self.snippet_preprocess(result['snippet_text'])
                
                self.add_terms(snippet['text'])
                yield snippet
            
        # generate the new url request based on the result
        yield self.new_search_request()
            
    def snippet_preprocess(self, text):
        # preprocess the snippet text
        text = re.sub('<[^>]*>', '', text) # remove tags
        text = re.sub('\n', '', text) # remove \n
        text = re.sub('&#39;', '\'', text) # transform html symbol to apostophe
        text = re.sub('&nbsp;', '', text) # remove html symbol of space
        text = re.sub('\.\.\.', '', text) # remove three dots
        return text
    
    def remove_punctuation(self, text):
        #punc = '!"#$%&\()*+,./:;<=>?@[\\]^_`{|}~' # my custom punctuation, without apostrophe and dash
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        
        return regex.sub(' ', text)
    
    def add_terms(self, text):
        # add new terms based on the search result
        text = self.remove_punctuation(text);
        
        for term in text.split():
            if term not in self.terms_used:
                self.terms_new.add(term)