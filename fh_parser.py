from lxml import etree
import base64
import requests
from PIL import Image
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
    
def appendText(section,  text):
    if text:
        if section.text is None:
            section.text = text.strip()
        else:
            section.text += text.strip()

def appendTail(section,  tail):
    if tail:
        if section.tail is None:
            section.tail = tail.strip()
        else:
            section.tail += tail.strip()

def parseElem(elem,  section,  parent):
    last = section

    appendText(section,  elem.text)

    for it in elem.iterchildren():
        if it.tag == "a":
            href = it.get("href")
            if href is None:
                continue
            
            if href.startswith("https://www.forumhouse.ru/attachments/"):
                image = SubElement(section, 'image')
                image.set('xlink:href',  "#image" + str(len(Images)))
                Images.append(href)
                continue

            if href.startswith("mailto:"):
                linkText = SubElement(section, 'a')
                linkText.set('xlink:href',  href)
                linkText.text = href[len("mailto:"):]
                if it.tail:
                    linkText.tail = it.tail.strip()
                continue

            linkText = SubElement(section, 'a')
            linkText.set('xlink:href',  href)
            parseElem(it,  linkText,  section)
            last = linkText
            continue
        
        if it.tag == 'img':
            url = it.get("src")
            if url is not None:
                image = SubElement(section, 'image')
                image.set('xlink:href',  "#image" + str(len(Images)))
                Images.append(url)
                section = image
                appendTail(section,  it.tail)
            continue

        if it.tag == "b":
            strongText = SubElement(section, 'strong')
            last = parseElem(it,  strongText,  section)
            continue
        
        if it.tag == "br" or it.tag == "div":
            if it.tag == "div":
                itClass = it.get("class")

                if itClass is not None and itClass.strip() == "bbCodeBlock bbCodeQuote":
                    citeText = SubElement(parent, 'cite')
                    citeTextAuthor = SubElement(citeText, 'text-author')
                    citeTextParag = SubElement(citeText, 'p')
                    appendText(citeTextAuthor,  it.get("data-author"))
                    for it_aside in it.iterchildren("aside"):
                        for it_blockquote in it_aside.iterchildren("blockquote"):
                            last = parseElem(it_blockquote,  citeTextParag,  citeText)
            
                if itClass is not None and itClass.strip() == "quote":
                    last = parseElem(it,  section,  parent)
                    continue

            section = SubElement(parent, 'p');
            appendText(section,  it.tail)

            last = section
            continue
        
        if it.tag == "span":
            style = it.get("style")
            if style is not None and style == "text-decoration: line-through":
                strikethroughText = SubElement(section, 'strikethrough')
                last = parseElem(it,  strikethroughText,  section)
                continue

            last = parseElem(it,  section,  section)
            continue

        if it.tag == "i":
            spanText = SubElement(section, 'emphasis')
            last = parseElem(it,  spanText,  section)
            continue

        if it.tag == "script":
            appendTail(section,  it.tail)
            continue

        if it.tag == "noindex":
            last = parseElem(it,  section,  section)
            continue
    
    appendTail(last,  elem.tail)

    return last

fb2doc = Element('FictionBook')
fb2doc.set('xmlns',  'http://www.gribuser.ru/xml/fictionbook/2.0')
fb2doc.set('xmlns:xlink',  'http://www.w3.org/1999/xlink')
description = SubElement(fb2doc, 'description')

s = requests.Session()
cookie = {'uidfh':'X9WYvljJJaqWpymYVF8RAg==',  '_ym_uid':'1489182882854348927',  '_ym_isad':'2',  '_ga':'GA1.2.438686107.1489182881', 
   '_ym_visorc_25329920':'w',  'fh_auth_session_id':'Qn9eEqTnrnKl7bf60C7IlBKnOXJJh01AFCjzdj4C',  'xf_tb_authflag':'1'}

Images = []

for pageNumber in range(1, 201):
    url = "https://www.forumhouse.ru/threads/210023/page-" + str(pageNumber)
    req=s.get(url, cookies=cookie )

    parser = etree.HTMLParser()
    root = etree.fromstring(req.text.encode('utf-8'), parser=parser)

    body = SubElement(fb2doc, 'body')
    
    messageLists = root.xpath('//ol[@class = "messageList"]')
    for messageList in messageLists:
        messages = messageList.xpath('//li')
        for message in messages:
            author = ""
            isMessage = False;
            msgClass = message.get("class") ;
            if (msgClass is None) :
                continue
            
            msgClass = msgClass.strip();
            if (msgClass == 'message') :
                author = message.get("data-author")

            if len(author) == 0:
                continue
            
            mainSection = SubElement(body, 'section')

            title = SubElement(mainSection, 'title')
            titleP  = SubElement(title, 'p')
            titleP.text = author

            section = SubElement(mainSection, 'section')
            s_section = SubElement(section, 'p')

            messageContents = message.xpath('.//div[@class = "messageContent"]')
            for messageContent in messageContents:
                commentator=''
                quoteMsg = ''
                attributeTypes = messageContent.xpath('.//div[@class = "attribution type"]')
                for attributeType in attributeTypes:
                    commentator = attributeType.text.strip()
                    break;
                
                quoteContainers = messageContent.xpath('.//blockquote[@class = "quoteContainer"]')
                for quoteContainer in quoteContainers:
                    if quoteContainer.text is not None:
                        quoteMsg = quoteContainer.text.strip()
                
                if (quoteMsg != ''):
                    cite = SubElement(section, 'cite')
                    textAuthor = SubElement(cite, 'text-author')
                    textAuthor.text = commentator
                    parag = SubElement(cite, 'p')
                    parag.text = quoteMsg
                    
                articles = messageContent.xpath('.//article')
                for article in articles:
                    blockquotes  = article.xpath('.//blockquote[@class = "messageText SelectQuoteContainer ugc baseHtml"]')
                    for blockquote in blockquotes:
                        parseElem(blockquote,  s_section,  section)

basewidth= 650

i = 0
for image in Images:
#    continue
    binary = SubElement(fb2doc, 'binary')
    binary.set("id", "image" + str(i))
    binary.set("content-type", "image/jpeg")
    if not image.startswith("http:") and not image.startswith("https:"):
        image = "https://www.forumhouse.ru/" + image
    try:
        filename = 'temp.gif'
        f = open(filename,  "wb")
        f.write(s.get(image, cookies=cookie).content)
        f.close()
        try:
            img = Image.open(filename)
            if img.size[1] > basewidth:
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), Image.ANTIALIAS)
            img.save(filename,  quality = 50)
            image_file = open(filename,  'rb')
            binary.text = base64.b64encode(image_file.read()).decode()
        except :  # This is the correct syntax
            i = i + 1
            continue
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        i = i + 1
        continue
        
    i = i+1

print (prettify(fb2doc))