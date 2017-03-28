from lxml import etree
import os
import base64
import requests
from PIL import Image
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom

fromPage = 1
toPage = 13
thread = 49978
outFb2FileName = "Filosofiya_doma.fb2"
prettyPrint = True
saveOnlyAuthor = ["lt654"]

baseImageWidth = 1000
imageQuality = 35
convertToGrayscale = True
minImageSizeForConverting = 4096

def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=" ")

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

def addImage(image,  url):
    if url in Images:
        image.set('xlink:href',  "#image" + str(Images.index(url)))
    else:
        image.set('xlink:href',  "#image" + str(len(Images)))
        Images.append(url)

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
                addImage(image, href)
                continue

            if href.startswith("attachments/"):
                image = SubElement(section, 'image')
                addImage(image, href)
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
                addImage(image, url)
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

                if itClass:
                    if itClass.strip() == "bbCodeBlock bbCodeQuote":
                        citeText = SubElement(parent, 'cite')
                        citeTextAuthor = SubElement(citeText, 'text-author')
                        citeTextParag = SubElement(citeText, 'p')
                        appendText(citeTextAuthor,  it.get("data-author"))
                        for it_aside in it.iterchildren("aside"):
                            for it_blockquote in it_aside.iterchildren("blockquote"):
                                last = parseElem(it_blockquote,  citeTextParag,  citeText)
                
                    if itClass.strip() == "quote":
                        last = parseElem(it,  section,  parent)
                        continue
                    
                    if itClass.strip() == "boxModelFixer primaryContent" or itClass.strip() == "thumbnail Tooltip" :
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

        if it.tag == "noindex" or it.tag == "ul" or it.tag == "li":
            last = parseElem(it,  section,  section)
            continue
    
    appendTail(last,  elem.tail)

    return last

fb2doc = Element('FictionBook')
fb2doc.set('xmlns',  'http://www.gribuser.ru/xml/fictionbook/2.0')
fb2doc.set('xmlns:xlink',  'http://www.w3.org/1999/xlink')
description = SubElement(fb2doc, 'description')

s = requests.Session()
cookie = {'fh_auth_session_id':'Qn9eEqTnrnKl7bf60C7IlBKnOXJJh01AFCjzdj4C',  'xf_tb_authflag':'1'}

Images = []

body = SubElement(fb2doc, 'body')

for pageNumber in range(fromPage, toPage + 1):
    url = "https://www.forumhouse.ru/threads/" + str(thread) + "/page-" + str(pageNumber)
    print("Parse page " + str(pageNumber) + " from " + str(toPage - fromPage + 1))
    req=s.get(url, cookies=cookie )

    parser = etree.HTMLParser()
    root = etree.fromstring(req.text.encode('utf-8'), parser=parser)

    pageSection = SubElement(body, 'section')
    pageTitle = SubElement(pageSection, 'title')
    pageTitleP  = SubElement(pageTitle, 'p')
    pageTitleP.text = "Page " + str(pageNumber)

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

            if not author or len(author) == 0:
                continue

            if (len(saveOnlyAuthor) > 0) and (author not in saveOnlyAuthor):
                continue
            
            mainSection = pageSection

            s_section = SubElement(mainSection, 'p')
            title = SubElement(s_section, 'strong')
            title.text = author

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
                    cite = SubElement(mainSection, 'cite')
                    textAuthor = SubElement(cite, 'text-author')
                    textAuthor.text = commentator
                    parag = SubElement(cite, 'p')
                    parag.text = quoteMsg
                
                lastMessage = s_section
                articles = messageContent.xpath('.//article')
                for article in articles:
                    blockquotes  = article.xpath('.//blockquote[@class = "messageText SelectQuoteContainer ugc baseHtml"]')
                    for blockquote in blockquotes:
                        lastMessage = parseElem(blockquote,  s_section,  mainSection)

                attachedFiles = messageContent.xpath('.//div[@class = "attachedFiles"]')
                for attachedFile in attachedFiles:
                    parseElem(attachedFile,  lastMessage,  s_section)

            SubElement(mainSection, 'empty-line')
            SubElement(mainSection, 'empty-line')

filename = 'temp_image.jpeg'
i = 0
for image in Images:
    print("Download image " + str(i) + " from " + str(len(Images)))
    binary = SubElement(fb2doc, 'binary')
    binary.set("id", "image" + str(i))
    binary.set("content-type", "image/jpeg")
    if not image.startswith("http:") and not image.startswith("https:"):
        image = "https://www.forumhouse.ru/" + image
    try:
        f = open(filename,  "wb")
        f.write(s.get(image, cookies=cookie).content)
        f.close()
        try:
            if os.stat(filename).st_size > minImageSizeForConverting:
                img = Image.open(filename)
                if convertToGrayscale:
                    img = img.convert('L')
                if img.size[1] > baseImageWidth:
                    wpercent = (baseImageWidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    img = img.resize((baseImageWidth, hsize), Image.ANTIALIAS)
                img.save(filename, format = img.format, quality = imageQuality)
            image_file = open(filename,  'rb')
            binary.text = base64.b64encode(image_file.read()).decode()
        except : 
            pass
    except requests.exceptions.RequestException as e:
        pass
    i = i+1

os.remove(filename)

print("Saving to file: " + outFb2FileName)
f = open(outFb2FileName,  "wb")
if prettyPrint:
    f.write(str.encode(prettify(fb2doc)))
else:
    f.write(ElementTree.tostring(fb2doc, 'utf-8'))
f.close()
print("Done")
