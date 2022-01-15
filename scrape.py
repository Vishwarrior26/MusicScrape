from datetime import date, datetime
import datetime
from bs4 import BeautifulSoup
from operator import itemgetter
import pandas as pd
import math
import requests
import re
import unidecode


class scrape:

    # Change var names to conform to snake_case
    """" This is the constructor docstring """

    def __init__(self, size=50, start="TODAY", end="NONE", user="vishwarrior"):
        self.setUser(user)
        self.setTime(start, end)
        self.setSize(size)

    def __getVeryStart(self):
        self.url = "https://www.last.fm/user/" + self.user + "/library/"
        req = requests.get(self.url)
        soup = BeautifulSoup(req.text, "html.parser")
        description = soup.find_all(class_="pagination-page")
        self.url += "?page=" + \
            str(re.findall('[0-9]+', str(description[-1]))[-1])
        req = requests.get(self.url)
        soup = BeautifulSoup(req.text, "html.parser")
        description = soup.find_all(class_="date-heading")
        pieces = str(description[-1])[25:-5].split(" ")
        month = f"{datetime.datetime.strptime(pieces[2], '%B').month:02}"
        day = f"{int(pieces[1]):02}"
        year = pieces[3]
        return year + "-" + month + "-" + day

    def __info(self, type):
        self.url = "https://www.last.fm/user/" + self.user + "/library/" + \
            type + "?from=" + self.start + "&to=" + self.end
        urls = [self.url]
        if self.size is None:
            req = requests.get(self.url)
            soup = BeautifulSoup(req.text, "html.parser")
            description = soup.find_all(class_="pagination-page")
            try:
                self.pages = int(re.findall(
                    '[0-9]+', str(description[-1]))[-1])
            except:
                self.pages = 1
        for x in range(2, self.pages + 1):
            urls.append(self.url + "&page=" + str(x))
        info = []
        for tempUrl in urls:
            req = requests.get(tempUrl)
            soup = BeautifulSoup(req.text, "html.parser")
            description = soup.find_all("meta", property="og:description")
            if len(description) > 1:
                temp = str(description[1])
                # Use Regex to find artist that has quotes in it?
                if '"Weird Al"' in temp:
                    init = temp.find("content='") + 9
                    fini = temp.find("' property", init + 1)
                else:
                    init = temp.find('content="') + 9
                    fini = temp.find('" property', init + 1)
                templist = temp[init:fini].split("), ")
                templist[-1] = templist[-1][:-1]
                for temper in templist:
                    play = int(temper.split(" ")[-1][1:])
                    unsplit = temper[:temper.find(str(play)) - 2]
                    if type != 'artists':
                        splitter = unsplit.find('—')
                        artist = unsplit[:splitter - 1]
                        kind = unsplit[splitter + 2:]
                        info.append([artist, kind, play])
                    else:
                        info.append([unsplit, play])
        for temp in info:
            temp[0] = temp[0].replace("&quot;", " ").lstrip(' ')
            temp[0] = temp[0].replace("&amp;", "&")
            temp[0] = unidecode.unidecode(temp[0])
            temp[-2] = unidecode.unidecode(temp[-2])
            temp[-2] = temp[-2].replace("&amp;", "&")
            temp[-2] = temp[-2].replace("&quot;", " ").lstrip(' ')
        return info[:self.size]

    def setSize(self, size):
        if size != "MAX":
            self.size = int(size)
            self.pages = int(math.ceil(self.size / 50))
        else:
            self.size = None

    def setTime(self, start, end="NONE"):
        self.start = start
        if start == "TODAY":
            self.start = str(date.today())
        elif start == "ALL":
            self.all = True
            self.start = self.__getVeryStart()
            end = "TODAY"
        if end == "NONE":
            self.end = self.start
        elif end == "TODAY":
            self.end = str(date.today())
        else:
            self.end = end

    def setUser(self, user):
        self.user = user
        try:
            if self.all == True:
                self.setTime("ALL", self.end)
        except:
            pass

    def artistInfo(self):
        return self.__info('artists')

    def albumInfo(self):
        return self.__info('albums')

    def trackInfo(self):
        return self.__info('tracks')

    def artistCounts(self):
        artists = []
        for temp in self.trackInfo():
            artist = temp[0]
            if artist not in (row[0] for row in artists):
                artists.append([artist, 1])
            else:
                for row in artists:
                    if row[0] == artist:
                        row[-1] += 1
        return sorted(artists, key=itemgetter(-1), reverse=True)

    def scrobblesInfo(self):
        self.url = "https://www.last.fm/user/" + self.user + "/library?from=" + \
            str(self.start) + "&to=" + str(self.end)
        req = requests.get(self.url)
        soup = BeautifulSoup(req.text, "html.parser")
        description = soup.find_all(class_="metadata-display")
        if len(description) > 0:
            temp = str(description[0])
            self.total = int("".join(str(x) for x in re.findall(
                "[0-9]", temp[temp.find(">") + 1:temp.find("<", 1)])))
            return self.total

    def __dailyInfo(self, info):
        results = []
        origStart = self.start
        origEnd = self.end
        for day in pd.date_range(start=self.start, end=self.end):
            curday = str(day.date())
            self.setTime(curday)
            results.append([curday, info()])
        self.setTime(origStart, origEnd)
        return results

    def dailyArtists(self):
        return self.__dailyInfo(self.artistInfo)

    def dailyAlbums(self):
        return self.__dailyInfo(self.albumInfo)

    def dailyTracks(self):
        return self.__dailyInfo(self.trackInfo)

    def __specInfo(self, search, info, index=0):
        results = []
        origSize = self.size
        self.setSize("MAX")
        for x in info():
            if x[index].lower() == search.lower():
                results.append(x)
        self.setSize(origSize)
        return results

    def specArtist(self, artist):
        return self.__specInfo(artist, self.artistInfo)

    def specAlbum(self, album):
        return self.__specInfo(album, self.albumInfo, -2)

    def specAlbumArtist(self, artist):
        return self.__specInfo(artist, self.albumInfo)

    def specTrack(self, track):
        return self.__specInfo(track, self.trackInfo, -2)

    def specTrackArtist(self, artist):
        return self.__specInfo(artist, self.trackInfo)
