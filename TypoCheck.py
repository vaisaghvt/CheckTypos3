#/usr/bin/python

import sublime
import sublime_plugin
import re
import threading
import os
from collections import defaultdict

import re

def getHashCode(region):
    return "-".join([str(region.begin()), str(region.end())])

def checkPattern(option, match, completeBuffer, phrase):
    # print phrase
    if option == 'a':
        # print 'checking acronym'
        return isAcronym(phrase)
    elif option == 'b':
        # print 'checking acronym'
        return afterAcronym(match, completeBuffer)
    elif option == 'c':
        # print 'checking comment'
        return isComment(match, completeBuffer)
    elif option == 'e':
        # print 'checking equation'
        return isEquation(match, completeBuffer)
    elif option == 'p':
        return isPicture(match, completeBuffer)
    elif option == 'b':
        return isTable(match, completeBuffer)
    elif option == 'h':
        return isInHyperLink(phrase)
    elif option == 'm':
        return isInMail(phrase)
    elif option == 'r':
        return isInRefCiteOrLabel(phrase)
    elif option == 'f':
        return isLikelyFile(phrase)


def isLikelyFile(phrase):
    if re.search(r"(\\input\{.*?\})|(\\bibliography\{.*?\})", phrase) is not None:
        return True
    return False


def isInRefCiteOrLabel(phrase):
    # print phrase
    if re.search(r"(\\ref\{.*?\})|(\\label\{.*?\})|(\\cite\{.*?\})||(\\eqref\{.*?\})", phrase) is not None:
        return True
    return False


def isInHyperLink(phrase):
    phrase = phrase.strip()
    if re.search(r"www\..*\.", phrase) is not None:
        return True

    # phrase = phrase[:-1]
    # print phrase
    # o = urlparse(phrase)
    # if len(o.netloc) >0 :
    #     return True
    return False


def isInMail(phrase):
    if re.search(r".*@.*\.", phrase) is not None:
        return True
    return False


def isAcronym(phrase):
    '''Returns a true if the match is an acronym'''
#    print "testing if", phrase, "is an acronym"
    if phrase.rfind('i.e.') != -1 or phrase.rfind('e.g.') != -1 or phrase.rfind('etc.') != -1:
        return True
    else:
        return False


def afterAcronym(match, completeBuffer):
    '''Returns a true if the match is an acronym'''
#    print "testing if", phrase, "is an acronym"
    if match.start() > 2:
        char = completeBuffer[match.start()-2]
        if char == '.':
            stringAsList = []
            i = match.start() - 2
            while completeBuffer[i] != ' ' and i != 0:
                stringAsList.insert(0, completeBuffer[i])
                i = i-1
            string = ''.join(stringAsList)
            if string.rfind('i.e.') != -1 or string.rfind('e.g.') != -1:
        #        print "returning true"
                return True
    return False


def isInCite(phrase):
    '''Returns a true if the match is in Cite'''
    if(phrase.rfind(r'\cite') == 0):
        return True
    else:
        return False


def isPicture(match, completeBuffer):
    end = completeBuffer[0:match.start()].rfind(r'\end{figure}')
    pos = 0
    while end != -1:
        pos = end+3
        # print pos, 'completeBuffer', completeBuffer[pos:match.start()]
        end = completeBuffer[pos:match.start()].rfind(r'\end{figure}')
        # print '*******'
    beg = completeBuffer[pos:match.start()].rfind(r'\begin{figure}')
    if(beg != -1):
        return True
    return False


def isTable(match, completeBuffer):
    end = completeBuffer[0:match.start()].rfind(r'\end{table}')
    pos = 0
    while(end != -1):
        pos = end+3
        # print pos, 'completeBuffer', completeBuffer[pos:match.start()]
        end = completeBuffer[pos:match.start()].rfind(r'\end{table}')
        # print '*******'
    beg = completeBuffer[pos:match.start()].rfind(r'\begin{table}')
    if beg != -1:
        return True
    return False


def isEquation(match, completeBuffer):
    if (inLineEquation(match, completeBuffer) or inEquationBody(match, completeBuffer)):
        return True
    else:
        return False


#Obsolete : to be replaced
def inLineEquation(match, completeBuffer):
    """ Returns true if in incompleteBuffer equation"""
    hasDollarTagBefore=False
    for i in range(match.start()-1,-1,-1):
        if completeBuffer[i] == '\n':   # TODO : replace this something else.
            break;
        if completeBuffer[i] == '$':
            hasDollarTagBefore=True
            break
    if hasDollarTagBefore:
        for i in range(match.end(),len(completeBuffer),1):
            if completeBuffer[i] == '\n':   # TODO : replace this something else.
                break;
            if completeBuffer[i] == '$':
                return True
    return False

# Issue : ignores end equations that are commented out.
def inEquationBody(match, completeBuffer):
    # print 'checking equation', match.start()-1
    end= completeBuffer[0:match.start()].rfind(r'\end{equation}') # Find the end of last equation
    pos= 0
    while(end!=-1):     # If it found some other equation in the file, keep finding till there are
                        # no  more end equations after the pos position
        pos= end+3
        # print pos, 'completeBuffer', completeBuffer[pos:match.start()]
        end= completeBuffer[pos:match.start()].rfind(r'\end{equation}')
        # print '*******'
    beg=completeBuffer[pos:match.start()].rfind(r'\begin{equation}')
    if(beg!=-1):
        return True
    return False


def isComment(match, completeBuffer):
    for i in range(match.start()-1,-1,-1):
        # print completeBuffer[i]
        if completeBuffer[i] == '\n':
            break
        if completeBuffer[i] == '%':
            return True
    return False

patterns = (
    # r'\\(sub)+section':["ONLY FIRST WORD CAPITALIZED IN SUBSECTIONS", 'c', convertFirstLetterToCapital],
    {"regex": r'((?<=(\\subsection\{))|(?<=(\\subsubsection\{))|(?<=(\\paragraph\{))|(?<=(\\subparagraph\{)))(([^A-Z](.*?))|([A-Z](.*?)[A-Z](.*?)))(?=\})',
     "description": 'Sentence Case For Subsections And Below',
     "tags": 'c'},
    {"regex": r'((?<=(\\section\{))|(?<=(\\chapter\{)))((|(.*) )[a-z].*)(?=\})',
     "description": 'Title Case For Sections And Chapters',
     "tags": 'c'},
    {"regex": r'( +)([\.,;:])',
     "description": 'Space Before Punctuation',
     "tags": 'acehmrfp'},
    {"regex": r'((\.)(?![\s\d\]\}\)]))|([,;:\?\]\)\}])(?=[a-zA-Z0-9])',
     "description": 'No Space After Punctuation',
     "tags": 'acehmrfp'},
    {"regex": r'((?<=(\.\s))|(?<=(\n\n))|(?<=\A))[a-z]',
     "description": 'Missing Capitalization Of First Word After Full Stop',
     "tags": 'acehmpb'},
    {"regex": r'(\s*)(?<!~)((\\cite)|(\\ref))',
     "description": 'Tilde Mark Needed Before Cite / Ref',
     "tags": 'ac'},
    {"regex": r'(chapter)(~\\ref)',
     "description": 'Capitalize C In Chapter',
     "tags": 'c'},
    {"regex": r'(section)(~\\ref)',
     "description": 'Capitalize S In Section',
     "tags": 'c'},
    {"regex": r'(?i)((?<=\s)|(?<=^))([A-Za-z][A-Za-z ]*)([^\w\d]+)\2((?=([ \n\.,;]))|(?=$))',
     "description": 'Repeated Phrase',
     "tags": 'ce'},
)

def syntax_name(view):
    syntax = os.path.basename(view.settings().get('syntax'))
    syntax = os.path.splitext(syntax)[0]
    return syntax

def extractPhrase(match, line):
    """Returns the phrase which was matched. Rather than just the matched pattern, it returns
    the complete phrase in which the match occured """

    startCount = 0
    endCount = len(line)
    for i in range(match.start() - 1, -1, -1):
        if line[i] == ' ' or line[i] == '\n' or line[i] == '\\':
            startCount = i
            break
    for i in range(match.end(), len(line), 1):
        if line[i] == ' ' or line[i] == '\n' or line[i] == '\\':
            endCount = i
            break
    return line[startCount:endCount]


affectedRegions=defaultdict(list)

def last_selected_lineno(view):
    viewSel = view.sel()
    if not viewSel:
        return None
    return view.rowcol(viewSel[0].end())[0]

class HighlightMistakesCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        self.view = view
        self.regionsToHighlight=[]
        self.myKey = "CheckTypoKey"

    def run(self, edit, *args, **kwargs):
        if syntax_name(self.view) == "LaTeX":
            # if self.view.id not in affectedRegions or last_selected_lineno(self.view) in affectedRegions[self.view.id]:
            if not args or "full_test" not in args:

                # self.view.erase_status(self.myKey)
                self.viewMatches = []
                self.matchIterators = []
                self.patternList = []
                self.recalculateMatches()
                # print(self.completeBuffer)
                self.mainThread = threading.Thread(target=self.processBuffer)
                self.mainThread.start()
                # self.processBuffer([completeBuffer])
            else:
                self.displayCurrentError()
                self.higlightAllRegions()

    def recalculateCompleteBuffer(self):
        # print("recalculating buffers")
        regions = self.view.find_all(".*")
        self.completeBuffer = '\n'.join(map(self.view.substr, regions))

    def recalculateMatches(self):
        self.recalculateCompleteBuffer()
        # print("recalculating matches")

        regionToRegexMatchAndPatternMapping = {}
        listOfRegions = []

        for pattern in patterns:  # for each pattern
            regexPattern = pattern["regex"]
            # regexPattern = pattern["regex"]
            #     # print(regexPattern)
            regex = re.compile(regexPattern)
            viewMatchesFound = self.view.find_all(regexPattern)


            for count, match in enumerate(regex.finditer(self.completeBuffer)):
                correspondingView = viewMatchesFound[count]

                regionToRegexMatchAndPatternMapping[getHashCode(correspondingView)] = (match, pattern)
                listOfRegions.append(correspondingView)


        listOfRegions = sorted(listOfRegions, key=(lambda region: region.begin()))

        self.patternList = []
        self.matchIterators = []
        self.viewMatches = []

        for region in listOfRegions:
            matchingRegex = regionToRegexMatchAndPatternMapping.get(getHashCode(region))[0]
            pattern = regionToRegexMatchAndPatternMapping.get(getHashCode(region))[1]

            self.patternList.append(pattern)
            self.matchIterators.append(matchingRegex)
            self.viewMatches.append(region)





    def higlightAllRegions(self):
        self.view.add_regions("mark", self.regionsToHighlight, "comment", "dot",
                sublime.DRAW_OUTLINED)
        for region in self.regionsToHighlight:
            affectedRegions[self.view.id()].append(self.view.rowcol(region.begin())[0])

    def displayCurrentError(self):
        lineno = last_selected_lineno(self.view)
        messagesToPrint= []
        if lineno and self.regionsToHighlight:
            for region in self.regionsToHighlight:
                if self.view.rowcol(region.begin())[0] == lineno:
                    messagesToPrint.append(self.descriptionStringList[region.begin()])


        if messagesToPrint:
            self.view.set_status(self.myKey, "; ".join(messagesToPrint))
        else:
            self.view.set_status(self.myKey, "Possible errors found")

    def processBuffer(self):
        problemsFound = False


        tagExceptionMatch = False
        self.regionsToHighlight =[]
        self.descriptionStringList ={}
        while len(self.viewMatches) > 0:
            regexMatch = self.matchIterators.pop(0)
            self.currentMatchedRegionInView = self.viewMatches.pop(0)
            pattern = self.patternList.pop(0)
            for option in pattern["tags"]:
                phrase = extractPhrase(regexMatch, self.completeBuffer)
                if checkPattern(option, regexMatch, self.completeBuffer, phrase):
                    # print 'tagExceptionMatch true'
                    tagExceptionMatch = True
                    break
            if tagExceptionMatch:
                tagExceptionMatch = False
                continue
            problemsFound = True
            self.regionsToHighlight.append(self.currentMatchedRegionInView)

            lineno = self.currentMatchedRegionInView.begin()

            self.descriptionStringList[lineno]= pattern["description"]

        if not problemsFound:
            self.higlightAllRegions()
            self.view.set_status(self.myKey, 'No mistakes found. Good Stuff!')
        else:
            self.higlightAllRegions()
            self.displayCurrentError()

class BackgroundLinter(sublime_plugin.EventListener):
    '''This plugin controls a linter meant to work in the background
    to provide interactive feedback as a file is edited. It can be
    turned off via a setting.
    '''

    def __init__(self):
        super(BackgroundLinter, self).__init__()
        self.lastSelectedLineNo = -1


    def on_post_save(self, view):
        view.run_command("highlight_mistakes")

    def on_load(self, view):
        view.run_command("highlight_mistakes")
    # def on_selection_modified(self, view):
    #     if view.is_scratch():
    #         return

    # def on_selection_modified(self, view):
    #     # pass
    #     view.run_command("highlight_mistakes", {"full_test":True})
    #     # view.run_command("highlight_mistakes")

