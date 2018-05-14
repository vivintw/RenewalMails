import pyDes
import base64
import json
import requests
import time
import datetime
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

    def __parse_form_inputs(self,result):
            payload = {}

            soup = BeautifulSoup(result, 'html.parser')
            f1 = soup.find_all('form')[0]
            for i in f1.find_all('input'):
                attributes = i.attrs
                payload[attributes['name']] = ""
                if 'value' in attributes :
                    payload[attributes['name']] = attributes['value']
            return payload

    def extract(self):
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        #TODO parse data into csv data and return csv data
        url = "https://ipartner.icicilombard.com/Webpages/CorporateApp/LandingPage.aspx?GUID="+self.guid
        res = self.session.get(url)
        payload = self.__parse_form_inputs(res.text)
        time.sleep(1)

        url = "https://ipartner.icicilombard.com/WebPages/SwapSession.aspx"
        res = self.session.post(url,data=payload)
        # sanity check make sure the login was successful
        if not 'welcome' in res.url:
            print "unable to login"
            return

        url = "https://ipartner.icicilombard.com/WebPages/Agents/RenewalPolicies.aspx"
        res = self.session.get(url)
        payload = self.__parse_form_inputs(res.text)
        payload['ctl00$headA$motorQuote$txtPolicyNo'] = ""
        payload['ctl00$headA$motorQuote$PolicyLengthExtender_ClientState'] = ""
        payload['ctl00$headA$motorQuote$vehicleType'] =  'rdbNew'
        payload['ctl00$headA$motorQuote$prodGrop'] = 'rdbCar'
        payload['ctl00$headA$motorQuote$ddEngineChasisNo'] = '0'
        payload['HiddenInput'] = ""
        payload['ctl00$ContentPlaceHolder1$ImageButton1.y'] = '11'
        payload['ctl00$ContentPlaceHolder1$ddProductCategory'] = '1'
        payload['ctl00$headA$motorQuote$ValidatorCalloutExtender1_ClientState'] = ""
        payload['ctl00$ToolkitScriptManager1'] = 'ctl00$ContentPlaceHolder1$updpnlTagging|ctl00$ContentPlaceHolder1$ImageButton1'
        payload['ctl00$ContentPlaceHolder1$ImageButton1.x'] = '72'
        payload['ctl00_ToolkitScriptManager1_HiddenField']= ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e'
        payload['__ASYNCPOST']=  'true'
        payload['ctl00$headA$motorQuote$txtEngineChasisNo'] = ""
        payload['PageLoadedHiddenTxtBox'] =  'Set'
        payload['ctl00$ContentPlaceHolder1$ddProductSubCategory'] = '0'

        today = datetime.datetime.today()
        payload['ctl00$ContentPlaceHolder1$ddMonth'] = str(today.month)
        payload['ctl00$ContentPlaceHolder1$ddYear'] =  str(today.year)

        time.sleep(1)
        res = self.session.post(url,data=payload)

        soup = BeautifulSoup(res.text, 'html.parser')
        tables = soup.find_all('table')
        table_data = []
        # only tables 8,9,10 are data
        for table in tables[8:]:
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    curr_cols = []
                    for i,c in enumerate(cols):
                        # get links instead of text of the specified columns
                        if i in [7]:
                            curr_cols.append('https://ipartner.icicilombard.com' + c.find('a').attrs['href'])
                        else:
                            curr_cols.append(c.text)
                    table_data.append(curr_cols)

        #get the vehicle type number from show RN
        output_table = []
        for table in table_data:
            print "fetching : ",table[7]
            res = self.session.get(table[7])
            soup = BeautifulSoup(res.text, 'html.parser')
            _table = soup.find('table',{'id' : 'tblVehicleDetails'})
            output_table.append(table[:-1] + [ele.text for ele in _table.find_all('tr')[1].find_all('td')[:2]])

        return output_table




if __name__ == "__main__":
    c = icici()
    c.login("test","test")
    data = c.extract()
    time.sleep(2)
    c.logout()
    for i in data:
        print i
