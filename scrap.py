from logging import exception
import requests
from bs4 import BeautifulSoup
import json
import math
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as EX
# DOCUMENT 
# F AS FUNCTION 
# P AS PARAMETER 

#f(p): this saves the actual driver.source of your selenium driver as web.html, param = driver, options: write
def saveWebFile(driver):
    file = open('web.html', 'w')
    file.write(driver.page_source)
    file.close()
    
#f(): opens a file named "web.html" options: readonly
def getWebFile():
    return open('web.html','r')

#f(): opens a file named "movies.json" options: write
def saveJson(data):
    f = open('movies.json', 'w')    
    f.write(json.dumps(data))
    f.close
    
def saveCurrentLink(data):
    f = open('current.txt', 'w')
    f.write(data)
    f.close
def getCurrent():
    return open('current.txt', 'r')

#f(): retrieve a list of category(movies) links
def getWebMenuItems():
    url = "https://www.looke.com.br/"
    for intentos in range(10):
        try:
            webpage = requests.get(url)
            res = webpage.content
            webpage = BeautifulSoup(res, "lxml")
            menu = webpage.find_all("div", {"class":"menuItem"})
            menu_links = []
            for menu_category in menu:
                menu_pages = menu_category.find_all("a", {"class":"headerMenuItenDescription"})
                for menu_page in menu_pages:
                    menu_links.append(menu_page["href"].strip())
            return menu_links
        except requests.exceptions.ConnectionError:
            print("Couldnt Connect Attempts: ")
            time.sleep(5)
            continue
        else:
            break

#f(p): this saves the actual driver.source, param = urltosave
def saveSourceFromSelenium(url):
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)
    for intentos in range(10):
        try:
            if(url == "https://www.looke.com.br/movies/shows-para-cantar-junto"): #this actually doesnt have a content
                driver.close()
                break
            driver.get(url)
            wait = WebDriverWait(driver, 15) #more for slow network connections
            loading = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "media-image")))
            Y = driver.execute_script('return scrollY')
            max_Y = driver.execute_script('return scrollMaxY')
            while Y != max_Y:
                driver.execute_script('scrollTo(0, scrollMaxY)')
                Y = math.ceil(float(driver.execute_script('return scrollY')))
                time.sleep(1.5)
                max_Y = driver.execute_script('return scrollMaxY')
            time.sleep(10)
            saveWebFile(driver)
        except EX.TimeoutException:
            print("Timeout, retrying ")
            driver.close()
            time.sleep(5)
            continue
        except EX.WebDriverException:
            print("WebDriver Error, retrying")
            time.sleep(5)
            continue
        else:
            driver.close()
            break
    
#f(): scrap all urls from the movies listed in a file.html
def scrapUrlMovies():
    file = getWebFile()
    sopa = BeautifulSoup(file, 'lxml')
    lista_peliculas = sopa.find_all("div", {"class":"mediaContainer"})
    urls = []
    for peliculas in lista_peliculas:
        pelicula_url = peliculas.find("video")
        pelicula_url = "https://www.looke.com.br/" + pelicula_url["onclick"][16:].replace("')", "")
        urls.append(pelicula_url)
    return urls

#f(p): returns all data movie from an url, params = urlmovie
def scrapDataMovies(url):
    for intentos in range(10):
        try:
            res = requests.get(url)
            webpage = res.content
            sopa = BeautifulSoup(webpage, "lxml").find_all("div", {"class": "detailsMedia"})
            for info_movie in sopa:
                movie = {}
                cast = []
                crew = []
                nro_capitulos = 0
                title = info_movie.find("div", {"class": "detailTitle"}).get_text().split(' - ')
                if title:
                    movie['Title'] = title.pop(0)
                if title:
                    movie['Temporada'] = title.pop()

                movie['URL'] = url
                movie['Ano'] = info_movie.find("div", {"class": "detailsYear"}).get_text().split(' | ')[0].strip()
                movie['Pais'] = info_movie.find("div", {"class": "detailsYear"}).get_text().split(' | ')[1].strip()
                movie['Duracion'] = info_movie.find("div", {"class": "detailsYear"}).get_text().split(' | ')[2].strip()
                if info_movie.find_all_next("div", {"class": "movieActorsContainer"})[1]:
                    for directive in info_movie.find_all_next("div", {"class": "movieActorsContainer"})[1].find_all("a"):
                        crew.append(directive.get_text())
                if info_movie.find_all_next("div", {"class": "movieActorsContainer"})[0].find_all("a"):
                    for actor in info_movie.find_all_next("div", {"class": "movieActorsContainer"})[0].find_all("a"):
                        cast.append(actor.get_text())
                        if str(actor.get_text()) != "Não Disponível":
                            crew.append(actor.get_text())

                movie['Cast'] = cast
                if cast:
                    if cast[0] == "Não Disponível":
                        movie['Cast'] = ",".join(cast)
                movie['Crew'] = crew
                movie['Generos'] = info_movie.find(
                    "div", {"class": "detailsGenre"}).get_text().split(', ')

                for capitulos in info_movie.find_all_next("div", {"class": "episodeName"}):
                    nro_capitulos += 1
                movie['Episodios'] = nro_capitulos
                return movie
        except requests.exceptions.ConnectionError:
            print("Couldnt Connect")
            time.sleep(5)
            continue
        else:
            break

if __name__ == "__main__":
    fa = open('movies.json', 'r')
    e = fa.read()
    movies = json.loads(e)
    urls = []
    ROOT = "https://www.looke.com.br"
    CATEGORIAS_LINK = getWebMenuItems()
    remaining = len(CATEGORIAS_LINK)
    for link in CATEGORIAS_LINK:
        currentLink = link
        print(link)
        remaining -= 1
        print(remaining)
        for intentos in range(10):
            time.sleep(5)
            try:
                saveSourceFromSelenium(ROOT + link)
                urls = scrapUrlMovies()
                for url in urls:
                    movies.append(scrapDataMovies(url))
                saveJson(movies)
            except ConnectionError:
                print("fail gettin content, attempt ")
                time.sleep(5)
                continue
            else:
                break
    print("deleting duplicates..")
    unique = { each['URL'] : each for each in movies }.values()
    saveJson(list(unique))
    print("done")