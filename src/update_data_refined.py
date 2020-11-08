from requests import get
from bs4 import BeautifulSoup
import csv
import os 
from datetime import datetime


# Function used by the write_security_packages function that returns a list of package names that need to be updated and 
# the versions that they need to be updated to in order to have satisfied the requirements of the specified security update.
# Each element of the list is a string in the format: [package name]+" "+[package version]
# The last element of the list is the date that the security update was released.

def get_packages(headers, version, link):
    packages = []
    soup = BeautifulSoup(get("https://ubuntu.com"+link,headers = headers).content, "html.parser")
    date = soup.findAll("div", {"class" : "col-12"})[1].find("p").text.split(" ")
    month = str(datetime.strptime(date[1], "%B").month)
    if len(month) < 2:
        month = "0"+month
    date = "-".join([date[2],month,date[0]])
    for div in soup.findAll("div",{"class" : "col-8"}):
        if div.find("h2").text == "Update instructions": soup = div
    for idx in range(len(soup.findAll("h5"))):
        if soup.findAll("h5")[idx].text == version: 
            soup = soup.findAll("ul")[idx]
            break
    for package in soup.findAll("li"):
        packages.append(package.findAll("a")[0].text+" "+package.findAll("a")[1].text+"\n")
    packages.append(date+"\n")
    return packages


# Scrapes Ubuntu release data from "https://wiki.ubuntu.com/Releases". Returns a list of all currently supported releases of Ubuntu.

def get_current_releases(url, headers):
    soup = BeautifulSoup(get(url, headers = headers).content, "html.parser")
    current_table = []
    for row in soup.findAll('table')[1].findAll('tr'):
            row_output = []
            for cell in row.findAll('td'):
                row_output.append(cell)            
            current_table.append(row_output)
    current_releases = []
    for row in range(1,len(current_table)):
        support = current_table[row][4].text.strip().split(" ")
        release = current_table[row][3]
        #print(release.find('p'))
        if len(support) != 2: support = support[1:]
        if release.find('p').find('a') != None and (int(support[1]) > datetime.today().year or (support[1] == datetime.today().year and datetime.datetime.strptime(support[0], "%B").month < 4)):
            current_releases.append(current_table[row][0].text.strip())
    return current_releases


# Returns a list of all currently supported versions of Ubuntu.

def get_current_versions(current_releases):
    current_versions = []
    last_release = ""
    for release in current_releases:
        if last_release == "":
            last_release = ".".join(release.split(".")[:2])
            current_versions.append(last_release)
        elif release.startswith(last_release):
            continue
        else:
            last_release = ".".join(release.split(".")[:2])
            current_versions.append(last_release)
    return current_versions


# Writes the names of all of the latest releases of the currently supported versions of Ubuntu to a file called "latest_releases.txt".

def write_latest_releases(current_releases):
    latest_releases = []
    for idx in range(len(current_releases)):
        if idx == 0 or ".".join(current_releases[idx].split(".")[:2]).rstrip(" LTS") != ".".join(current_releases[idx-1].split(".")[:2]).rstrip(" LTS"):
            latest_releases.append(current_releases[idx]+"\n")
    f = open("latest_releases.txt","w")
    f.writelines(latest_releases)
    f.close()


# Scrapes security update data from "https://ubuntu.com/security/notices".
# Since this site has 24 pages at the time of writing and will only get larger, the function will stop either when all pages 
# have been scraped, or when an update from all current versions of Ubuntu has been scraped. It will likely be the latter as 
# this can often be achieved from just scraping the first page.
# The function will return a list of lists. Each sub list contains data from each security notice formatted as follows: 
# [[link to the security notice], [USN], [date released], [versions affected]].

def get_security_notices(url, headers, current_versions):
    page_number = 1
    soup = BeautifulSoup(get(url+str(page_number), headers = headers).content, "html.parser")

    security_notices = []
    all_found = False
    versions_found = []
    while soup.find("h1").text != "404: Page not found" and not all_found:
        for notice in soup.findAll("article",{"class":"notice"}):
            link = notice.find("a").get("href")
            usn = link.split("/")[3]
            date = notice.find("p").text
            versions = [version.text.strip() for version in notice.find("ul").findAll("li")]
            security_notices.append([link,usn,date,versions])
            for version in versions: 
                if len(version.split(" ")) != 2: version = " ".join(version.split(" ")[:2])
                if version not in versions_found: versions_found.append(version)
        check_done = True
        for version in current_versions: 
            if version not in versions_found:
                check_done = False
        if check_done: break
        page_number += 1
        soup = BeautifulSoup(get(url+str(page_number), headers = headers).content, "html.parser")
    return security_notices


# Creates a directory called sec_notices and files within the directory named after each of the currently supported versions of Ubuntu, eg. "20.04".
# The data from the get_packages function is written to each of these files according to which version it relates to.

def write_security_packages(headers, current_versions, security_notices):
    f = open("supported_versions.txt", "w")
    most_recent_security_updates = []
    if not os.path.exists('sec_notices'):
        os.makedirs('sec_notices')
    for version in current_versions:
        f.writelines(version + "\n")
        found = False
        notice = 0
        while notice < len(security_notices):
            for affected_version in security_notices[notice][3]:
                if affected_version.startswith(version):
                    most_recent_security_updates.append(security_notices[notice][0])
                    found = True
                    w = open("sec_notices/"+version.split(" ")[1], "w")
                    w.writelines(get_packages(headers, version, security_notices[notice][0]))
                    w.close()
                    break
            if found: break
            notice += 1


# Function used from outside this file to write the required Ubuntu data to files.

def get_ubuntu_data():
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    release_url     = "https://wiki.ubuntu.com/Releases"
    security_url = "https://ubuntu.com/security/notices?order=newest&details=execution&page="
    releases = get_current_releases(release_url, headers)
    versions = get_current_versions(releases)
    write_latest_releases(releases)
    notices = get_security_notices(security_url, headers, versions)
    write_security_packages(headers, versions, notices)

get_ubuntu_data()