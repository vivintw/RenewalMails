import pyDes
import base64
import json
import requests
import time
from bs4 import BeautifulSoup

class icici:
    #https://ipartner.icicilombard.com/WebPages/Resources/HtmlScripts/LoginJS.js

    def __init__(self):
        #-------------------------------------------------------------
        #var key = '01234ABCDEF6789GHIJKLMNO';//generateRandomeNo(24);
        #var iv = '01234ABC';//generateRandomeNo(8);
        #-------------------------------------------------------------
        self.key = '01234ABCDEF6789GHIJKLMNO'
        self.iv = '01234ABC'
        self.guid = None
        self.session = requests.session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.170 Safari/537.36'


    def __encrypt(self,data):
        #-------------------------------------------------------------
        #des(key, input, 1, 1, iv, 1);
        #encode64(des('01234ABCDEF6789GHIJKLMNO', 'hello', 1, 1, '01234ABC', 1)) = eM12K0OdKq8=
        #-------------------------------------------------------------
        des = pyDes.triple_des(self.key, IV=self.iv, padmode=pyDes.PAD_PKCS5,mode=pyDes.CBC)
        return base64.b64encode(des.encrypt(data))

    def __encrypt_string(self,username,password):
        abcL = self.__encrypt(username)
        #<option value="1">Retail Products</option>
        abcLA = self.__encrypt("1")
        abc = self.__encrypt(password)
        return "1-" + self.key + "-" + self.iv + "-" + abcL + "-" + abc + "-" + abcLA;

    def login(self,username,password):

        #need to get cookie from this url
        url ="https://ipartner.icicilombard.com/Login.htm"
        self.session.get(url)

        retVal = self.__encrypt_string(username,password)
        payload = json.dumps({"userDetails": retVal})
        self.session.headers['Content-Type'] = 'application/json; charset=utf-8'
        url = "https://ipartner.icicilombard.com/InternalServices/dataservice.asmx/AuthenticationUser"
        res = self.session.post(url,data=payload)
        self.guid = res.json()['d']
        return self.guid != None


    def logout(self):
        self.session.headers['Content-Type'] = 'text/html; charset=utf-8'
        url = "https://ipartner.icicilombard.com/WebPages/Logout.aspx?type=agent"
        res = self.session.get(url, allow_redirects=False)
        return '/Login.htm' in res.headers['location']

    def extract(self):
        url = "https://ipartner.icicilombard.com/Webpages/CorporateApp/LandingPage.aspx?GUID="+self.guid
        res = self.session.get(url)

        #TODO parse data into csv data and return csv data
        payload = {}

        soup = BeautifulSoup(res.text, 'html.parser')
        f1 = soup.find_all('form')[0]
        for i in f1.find_all('input'):
            attributes = i.attrs
            payload[attributes['name']] = ""
            if 'value' in attributes :
                payload[attributes['name']] = attributes['value']
        print json.dumps(payload,indent=4)

        time.sleep(1)

        url = "https://ipartner.icicilombard.com/WebPages/SwapSession.aspx"
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        res = self.session.post(url,data=payload)
        print res.content




if __name__ == "__main__":
    c = icici()
    print c.login("test","test")
    c.extract()
    time.sleep(2)
    print c.logout()
